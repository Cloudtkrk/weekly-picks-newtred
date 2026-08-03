/**
 * タイムセール設定依頼フォーム → スプレッドシート格納 (Google Apps Script)
 *
 * ■ 設置手順
 *  1. 下記 SHEET_ID の格納先スプレッドシートを開く
 *     https://docs.google.com/spreadsheets/d/1LpMX46K7PMveKiT92UqD6nor8NFxqSSNB0UPDOxAB4g/edit
 *  2. 拡張機能 → Apps Script を開き、このファイルの中身をすべて貼り付けて保存
 *  3. 右上「デプロイ」→「新しいデプロイ」→ 種類の選択(歯車)→「ウェブアプリ」
 *       説明          : timesale webhook
 *       次のユーザーとして実行 : 自分
 *       アクセスできるユーザー : 全員          ← ここが「全員」でないと受信できません
 *  4. 「デプロイ」を押し、初回のみ権限を承認 (「詳細」→「安全ではないページに移動」でOK)
 *  5. 表示される「ウェブアプリのURL」(https://script.google.com/macros/s/....../exec) をコピーし、
 *     Claudeに渡す or weekly_picks.py の CONFIG["timesale_webhook_url"] に貼って再生成する
 *
 * ■ 仕様
 *  - フォーム送信ごとに1行追記。シートが無ければヘッダー付きで自動作成する
 *  - 受信できる項目: account / product / shop / productId / slots[] / note / affiliate / pageUrl
 *  - スクリプトを更新したときは「デプロイ」→「デプロイを管理」→ 鉛筆 →
 *    バージョン「新バージョン」→ デプロイ (URLは変わりません)
 */

const SHEET_ID = '1LpMX46K7PMveKiT92UqD6nor8NFxqSSNB0UPDOxAB4g';
const SHEET_NAME = '依頼一覧';
const HEADERS = ['受付日時', 'TikTokアカウント', '商品名', 'ショップ', '商品ID',
                 '希望日程1', '希望日程2', '希望日程3', '備考', 'アフィリエイトリンク', '依頼ページ'];

function doPost(e) {
  try {
    const data = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    const sheet = getSheet_();
    const slots = data.slots || [];
    sheet.appendRow([
      new Date(),
      data.account || '',
      data.product || '',
      data.shop || '',
      "'" + (data.productId || ''),   // 商品IDが指数表記にならないよう文字列で保存
      slots[0] || '',
      slots[1] || '',
      slots[2] || '',
      data.note || '',
      data.affiliate || '',
      data.pageUrl || '',
    ]);
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

/** 疎通確認用: ブラウザでウェブアプリURLを開くと {"ok":true,"ping":true} が返る */
function doGet() {
  return json_({ ok: true, ping: true });
}

function getSheet_() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
