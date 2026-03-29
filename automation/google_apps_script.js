


const API_ENDPOINT = "https://your-server.com/api/train"; // ← replace
const SHEET_NAME = "SOP Automation";
const INCLUDE_SCENARIOS = false;

// Column indices (1-based, matching the sheet header row)
const COL = {
  SOP_NAME: 1,
  SOP_INPUT: 2,
  STATUS: 3,
  SUMMARY: 4,
  TRAINING_STEPS: 5,
  QUIZ: 6,
  SKILLS: 7,
  TRAINING_TIME: 8,
  CERTIFICATE_LINK: 9,
  ERROR: 10,
  TIMESTAMP: 11,
};

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🤖 SOP Automation")
    .addItem("▶ Run Automation (Pending rows)", "runAutomation")
    .addSeparator()
    .addItem("⏰ Enable Auto-Trigger (every 15 min)", "enableTimeTrigger")
    .addItem("🛑 Disable Auto-Trigger", "disableTimeTrigger")
    .addSeparator()
    .addItem("📋 View Trigger Status", "showTriggerStatus")
    .addToUi();
}

// ─────────────────────────────────────────────────────────────
//  MAIN AUTOMATION — processes every row where Status = "Pending"
// ─────────────────────────────────────────────────────────────
function runAutomation() {
  const sheet = getSheet_();
  const lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    showToast_("No data rows found. Add SOP rows first.", "Info");
    return;
  }

  let processed = 0;
  let errors = 0;

  for (let row = 2; row <= lastRow; row++) {
    const status = sheet.getRange(row, COL.STATUS).getValue().toString().trim();
    const sopText = sheet.getRange(row, COL.SOP_INPUT).getValue().toString().trim();
    const sopName = sheet.getRange(row, COL.SOP_NAME).getValue().toString().trim();

    // Skip rows that are not Pending or have no SOP text
    if (status.toLowerCase() !== "pending" || !sopText) continue;

    // Mark as Processing immediately so duplicate runs skip it
    sheet.getRange(row, COL.STATUS).setValue("⏳ Processing");
    SpreadsheetApp.flush(); // force write before API call

    try {
      const result = callTrainApi_(sopText);
      writeResultToSheet_(sheet, row, result);
      sheet.getRange(row, COL.STATUS).setValue("✅ Done");
      processed++;
    } catch (err) {
      sheet.getRange(row, COL.STATUS).setValue("❌ Error");
      sheet.getRange(row, COL.ERROR).setValue(err.message || String(err));
      errors++;
    }

    // Timestamp
    sheet.getRange(row, COL.TIMESTAMP).setValue(
      Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss")
    );

    SpreadsheetApp.flush();
  }

  const summary = `Processed: ${processed} row(s). Errors: ${errors}.`;
  showToast_(summary, "SOP Automation Complete");
  Logger.log(summary);
}

// ─────────────────────────────────────────────────────────────
//  API CALL — sends SOP text and returns parsed JSON
// ─────────────────────────────────────────────────────────────
function callTrainApi_(sopText) {
  const payload = JSON.stringify({
    sop_text: sopText,
    include_scenarios: INCLUDE_SCENARIOS,
  });

  const options = {
    method: "post",
    contentType: "application/json",
    payload: payload,
    muteHttpExceptions: true,
    timeout: 120000, // 2 minutes — AI calls can be slow
  };

  const response = UrlFetchApp.fetch(API_ENDPOINT, options);
  const statusCode = response.getResponseCode();
  const body = response.getContentText();

  if (statusCode !== 200) {
    throw new Error(`API returned ${statusCode}: ${body.substring(0, 300)}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(body);
  } catch (_) {
    throw new Error("API response was not valid JSON: " + body.substring(0, 200));
  }

  return parsed;
}

// ─────────────────────────────────────────────────────────────
//  WRITE RESULTS — maps API response fields to sheet columns
// ─────────────────────────────────────────────────────────────
function writeResultToSheet_(sheet, row, data) {
  // Summary — join bullet points
  const summaryText = (data.summary_points || [])
    .map((pt, i) => `${i + 1}. ${pt}`)
    .join("\n");

  // Training Steps — compact format
  const stepsText = (data.training_steps || [])
    .map((s, i) => {
      const step = `Step ${i + 1}: ${s.title || s.step || ""}\n  → ${s.description || s.instruction || ""}`;
      const tip = s.pro_tip ? `\n  💡 ${s.pro_tip}` : "";
      return step + tip;
    })
    .join("\n\n");

  // Quiz — question + correct answer only (keep sheet readable)
  const quizText = (data.quiz || [])
    .map((q, i) => {
      const options = (q.options || []).map((o, j) => `  ${String.fromCharCode(65 + j)}. ${o}`).join("\n");
      return `Q${i + 1}: ${q.question}\n${options}\n  ✅ Answer: ${q.answer || q.correct_answer || ""}`;
    })
    .join("\n\n");

  // Skills
  const skillsText = (data.skills_covered || []).join(", ");

  // Write all columns
  sheet.getRange(row, COL.SUMMARY).setValue(summaryText);
  sheet.getRange(row, COL.TRAINING_STEPS).setValue(stepsText);
  sheet.getRange(row, COL.QUIZ).setValue(quizText);
  sheet.getRange(row, COL.SKILLS).setValue(skillsText);
  sheet.getRange(row, COL.TRAINING_TIME).setValue(data.estimated_training_time || "");

  // Certificate link — populate if your API returns a URL, else leave note
  const certUrl = data.certificate_url || "";
  if (certUrl) {
    sheet.getRange(row, COL.CERTIFICATE_LINK).setValue(certUrl);
  } else {
    sheet.getRange(row, COL.CERTIFICATE_LINK).setValue("Generate via app.py");
  }

  // Clear any previous error
  sheet.getRange(row, COL.ERROR).clearContent();
}

//  onEdit TRIGGER (optional auto-trigger on status change)
//  Fires whenever someone changes a cell in the sheet.
//  Only processes the row if Status was manually set to "Pending".

function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  if (sheet.getName() !== SHEET_NAME) return;

  const col = e.range.getColumn();
  const row = e.range.getRow();
  const value = e.value;

  // Only trigger when the Status column is set to "Pending"
  if (col === COL.STATUS && value && value.toLowerCase() === "pending" && row > 1) {
    Utilities.sleep(500); // tiny delay to let user finish typing

    const currentStatus = sheet.getRange(row, COL.STATUS).getValue().toLowerCase();
    if (currentStatus === "pending") {
      // Process just this single row
      processSingleRow_(sheet, row);
    }
  }
}

//  SINGLE ROW PROCESSOR (used by onEdit)

function processSingleRow_(sheet, row) {
  const sopText = sheet.getRange(row, COL.SOP_INPUT).getValue().toString().trim();
  if (!sopText) return;

  sheet.getRange(row, COL.STATUS).setValue("⏳ Processing");
  SpreadsheetApp.flush();

  try {
    const result = callTrainApi_(sopText);
    writeResultToSheet_(sheet, row, result);
    sheet.getRange(row, COL.STATUS).setValue("✅ Done");
  } catch (err) {
    sheet.getRange(row, COL.STATUS).setValue("❌ Error");
    sheet.getRange(row, COL.ERROR).setValue(err.message || String(err));
  }

  sheet.getRange(row, COL.TIMESTAMP).setValue(
    Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss")
  );
  SpreadsheetApp.flush();
}

//  TIME-BASED TRIGGER — runs every 15 minutes automatically

function enableTimeTrigger() {
  // Remove existing to avoid duplicates
  disableTimeTrigger();

  ScriptApp.newTrigger("runAutomation")
    .timeBased()
    .everyMinutes(15)
    .create();

  showToast_("Auto-trigger enabled. Runs every 15 minutes.", "Trigger Active");
}

function disableTimeTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "runAutomation") {
      ScriptApp.deleteTrigger(t);
    }
  });
  showToast_("Auto-trigger disabled.", "Trigger Removed");
}

function showTriggerStatus() {
  const triggers = ScriptApp.getProjectTriggers().filter(
    t => t.getHandlerFunction() === "runAutomation"
  );
  const msg = triggers.length > 0
    ? `✅ Auto-trigger is ACTIVE (${triggers.length} trigger(s)).`
    : "⏸ Auto-trigger is INACTIVE. Use the menu to enable it.";
  SpreadsheetApp.getUi().alert("Trigger Status", msg, SpreadsheetApp.getUi().ButtonSet.OK);
}


//  UTILITY HELPERS

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    throw new Error(`Sheet "${SHEET_NAME}" not found. Check the SHEET_NAME constant.`);
  }
  return sheet;
}

function showToast_(message, title) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, title, 5);
}


function setupSheetHeaders() {
  const sheet = getSheet_();
  const headers = [
    "SOP Name", "SOP Input (Text)", "Status",
    "Summary", "Training Steps", "Quiz",
    "Skills Covered", "Est. Training Time", "Certificate Link",
    "Error", "Processed At",
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length)
    .setFontWeight("bold")
    .setBackground("#1a1a2e")
    .setFontColor("#ffffff");
  sheet.setFrozenRows(1);
  showToast_("Headers created!", "Setup Complete");
}
