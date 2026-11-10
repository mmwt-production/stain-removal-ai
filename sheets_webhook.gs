// Google スプレッドシートを保存先にするための Apps Script
// 使い方は README_公開手順.md を参照。TOKEN は自分だけの合言葉に書き換えること。

const TOKEN = 'CHANGE_ME';
const SHEET_NAME = 'records';
const HEADERS = [
  'id', 'created_at', 'detected_color', 'spread_answer', 'texture_answer',
  'smell_answer', 'predicted_stain', 'is_correct', 'actual_stain',
  'actual_chemical', 'feedback_at',
];

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) sh = ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
  }
  return sh;
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const req = JSON.parse(e.postData.contents);
    if (req.token !== TOKEN) return out_({ error: 'unauthorized' });
    const sh = sheet_();

    if (req.action === 'append') {
      sh.appendRow(HEADERS.map(h => (req.row[h] === undefined || req.row[h] === null) ? '' : req.row[h]));
      return out_({ ok: true });
    }

    if (req.action === 'update') {
      const last = sh.getLastRow();
      if (last < 2) return out_({ error: 'not found' });
      const ids = sh.getRange(2, 1, last - 1, 1).getValues().map(r => String(r[0]));
      const idx = ids.indexOf(String(req.id));
      if (idx < 0) return out_({ error: 'not found' });
      const row = idx + 2;
      Object.keys(req.fields).forEach(k => {
        const col = HEADERS.indexOf(k);
        if (col >= 0) sh.getRange(row, col + 1).setValue(req.fields[k]);
      });
      return out_({ ok: true });
    }

    if (req.action === 'list') {
      const last = sh.getLastRow();
      if (last < 2) return out_({ rows: [] });
      const values = sh.getRange(2, 1, last - 1, HEADERS.length).getValues();
      const rows = values
        .filter(v => v[HEADERS.indexOf('feedback_at')] !== '')
        .map(v => {
          const o = {};
          HEADERS.forEach((h, i) => { o[h] = v[i] instanceof Date ? v[i].toISOString() : v[i]; });
          return o;
        });
      return out_({ rows: rows });
    }

    return out_({ error: 'unknown action' });
  } catch (err) {
    return out_({ error: String(err) });
  } finally {
    lock.releaseLock();
  }
}
