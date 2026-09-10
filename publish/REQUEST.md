# publish/ — 本公開のトリガー

このディレクトリは**本公開 (本番サイト更新 + Discord投稿) を発火させるためだけ**にある。
生成物でもサイトの一部でもないので、ここのファイルを読み込んでいる処理はない。

## 公開のしかた

`.github/workflows/weekly.yml` の `publish` ジョブは、次の**どちらか**で走る。

1. **Actionsタブから手動実行**
   Actions → 「Weekly Picks」→ Run workflow
2. **コミットメッセージを `publish:` で始めてプッシュ**
   このファイルの「公開ログ」に1行足し、`publish: 2026-09-07分を公開` のような
   メッセージでプッシュする。
   Actions画面を開けない環境 (Claudeのリモートセッション等) から公開するための経路。

どちらの場合も `publish` ジョブが以下を行う:

- `weekly_data_v1.py --auto input/ --html --post --top-per-cat 3` で本生成
- `index.html` / `challenge.html` を更新し、`build_tap.py` で `tap.html` と🤝タブを作り直す
- `archive/` / `data/` を保存し、`preview/` を削除して bot名義でコミット (`[skip ci]`)
- Discordへ1ジャンル上位3件を投稿 (Secret `DISCORD_WEBHOOK_URL`)

生成に失敗した場合はそこで止まり、**サイト更新もDiscord投稿も行われない**。

## 注意

- メッセージが `publish:` で始まる push は**プレビューを作らず、いきなり本公開する**。
  先に `input/` を更新してプレビューを確認し、内容がOKになってからこの経路を使うこと。
- `input/` の差し替えコミットのメッセージを `publish:` で始めないこと
  (プレビューを飛ばして公開されてしまう)。
- 判定が「含む」ではなく「で始まる」なのは、本文で公開手順に言及しただけの
  コミットが誤って公開してしまうのを防ぐため。

## 公開ログ

| 日付 (UTC) | 対象データ | 備考 |
|---|---|---|
