# input/ — Kalodataエクスポート置き場

ここに毎週のKalodataエクスポート3〜4ファイルを置いてコミット&プッシュすると、
GitHub Actions (`.github/workflows/weekly.yml`) が **プレビューだけ** を自動生成する
(`/preview/` で確認可。本番ページとDiscordはまだ更新されない)。

- `Kalodata_Product_*.xlsx` ×2 (売れ筋/新商品は「アップロード時間」で自動判別)
- `Kalodata_Video_*.xlsx` ×1〜2 (2つある場合は行数が多い方が通常動画。
  同じ件数でエクスポートした週は行数で判別できないため、GMV中央値が低い方を
  フォロワー少動画とみなす)

翌週は古いファイルを削除して新しいエクスポートに置き換えること。

## 公開の流れ (2段階)

1. ここにエクスポートをプッシュ → プレビューが `https://<Vercelドメイン>/preview/` に生成される
2. プレビューを確認してOKなら、Actionsタブ「Weekly Picks」→ **Run workflow** を実行
   → 本番ページ更新 (Vercelデプロイ) + Discord投稿 + アーカイブ保存が行われる

Actionsの自動トリガーは `input/**` 配下の変更のみ。コミットメッセージに `[skip ci]` を
含めるとプレビュー生成をスキップできる。
