/**
 * 알림메일 시트의 "대기" 행을 읽어, 해당 행의 수신주소(B열)로 메일 발송 후 "완료"로 갱신합니다.
 * 수신 주소는 프로그램 설정(설정 > 알림 수신 메일 주소)에서 입력한 값이 시트에 함께 기록됩니다.
 *
 * 설정 방법:
 * 1. 구글 시트에서 확장 프로그램 > Apps Script 열기
 * 2. 이 스크립트 전체를 붙여넣고 저장
 * 3. sendPendingNotificationEmails 함수를 한 번 수동 실행하여 권한 부여
 * 4. 배포 > 새 배포 > 웹 앱으로 배포 후 URL을 복사해 case-ing 설정에 붙여넣기
 * 5. 수신 주소는 case-ing 프로그램의 "설정" 창에서 입력합니다.
 */

/**
 * 웹 앱으로 배포 시, Python에서 이 URL로 POST 요청을 보내면 대기 행을 즉시 발송합니다.
 */
function doPost(e) {
  sendPendingNotificationEmails();
  return ContentService.createTextOutput('OK').setMimeType(ContentService.MimeType.TEXT);
}

const SHEET_NAME = '알림메일';
const COL_일시 = 1;       // A
const COL_수신주소 = 2;   // B
const COL_메일내용 = 3;   // C
const COL_발송상태 = 4;   // D
const HEADER_ROW = 1;

/**
 * 발송상태가 "대기"인 행을 찾아, 해당 행의 수신주소(B열)로 메일 발송 후 "완료"로 변경합니다.
 * 수동 실행: 함수 목록에서 sendPendingNotificationEmails 선택 후 실행.
 * 트리거: 1분마다 실행 등으로 설정 가능.
 */
function sendPendingNotificationEmails() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) return;

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  const dataRange = sheet.getRange(2, 1, lastRow, COL_발송상태);
  const rows = dataRange.getValues();
  const statusRange = sheet.getRange(2, COL_발송상태, lastRow, COL_발송상태);

  const subject = 'case-ing 최신 업데이트 내역';

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const status = String(row[COL_발송상태 - 1] || '').trim();
    if (status !== '대기') continue;

    const 일시 = row[COL_일시 - 1];
    const 수신주소 = String(row[COL_수신주소 - 1] || '').trim();
    const 메일내용 = row[COL_메일내용 - 1];

    if (!수신주소 || 수신주소.indexOf('@') === -1) {
      statusRange.getCell(i + 1, 1).setValue('건너뜀(수신주소없음)');
      continue;
    }
    if (!메일내용 || String(메일내용).trim() === '') {
      statusRange.getCell(i + 1, 1).setValue('건너뜀(내용없음)');
      continue;
    }

    try {
      const htmlBody = String(메일내용).trim();
      MailApp.sendEmail({
        to: 수신주소,
        subject: subject + ' (' + (일시 || '') + ')',
        htmlBody: htmlBody
      });
      statusRange.getCell(i + 1, 1).setValue('완료');
    } catch (e) {
      statusRange.getCell(i + 1, 1).setValue('실패: ' + (e.message || e.toString()).slice(0, 50));
    }
  }
}
