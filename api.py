"""
api.py — FastAPI REST endpoint for the SOP Training Engine.

Run:  uvicorn api:app --host 0.0.0.0 --port 8000
Test: curl -X POST http://localhost:8000/api/train \
        -H "Content-Type: application/json" \
        -d '{"sop_text": "Your SOP text here..."}'
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.sop_preprocessor import preprocess_sop, format_for_prompt
from core.ai_engine import generate_training_content
from core.scenario_engine import generate_scenarios

app = FastAPI(
    title="Nutrabay SOP Training Engine API",
    description="Transform SOPs into structured training content via AI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrainRequest(BaseModel):
    sop_text: str = Field(..., min_length=50, description="Raw SOP text (min 50 chars)")
    include_scenarios: bool = Field(False, description="Also generate interactive scenarios")


class TrainResponse(BaseModel):
    title: str
    objective: str
    summary_points: list[str]
    training_steps: list[dict]
    quiz: list[dict]
    skills_covered: list[str]
    estimated_training_time: str = ""
    scenarios: list[dict] = []


@app.get("/")
def root():
    return {
        "service": "Nutrabay SOP Training Engine",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/train": "Transform SOP text into training content",
        },
    }


@app.post("/api/train", response_model=TrainResponse)
def train(req: TrainRequest):
    """Transform raw SOP text into structured training content."""
    try:
        # Preprocess
        preprocessed = preprocess_sop(req.sop_text)
        prompt_text = format_for_prompt(preprocessed)

        # Generate training content (two-pass pipeline)
        data = generate_training_content(prompt_text)

        # Optionally generate scenarios
        scenarios = []
        if req.include_scenarios:
            scenarios = generate_scenarios(data)

        return TrainResponse(
            title=data.get("title", ""),
            objective=data.get("objective", ""),
            summary_points=data.get("summary_points", []),
            training_steps=data.get("training_steps", []),
            quiz=data.get("quiz", []),
            skills_covered=data.get("skills_covered", []),
            estimated_training_time=data.get("estimated_training_time", ""),
            scenarios=scenarios,
        )

    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
