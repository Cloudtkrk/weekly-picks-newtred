# input/ — Kalodataエクスポート置き場

ここに毎週のKalodataエクスポート3〜4ファイルを置いてコミット&プッシュすると、
GitHub Actions (`.github/workflows/weekly.yml`) が生成→サイト更新→Discord投稿まで自動実行する。

- `Kalodata_Product_*.xlsx` ×2 (売れ筋/新商品は「アップロード時間」で自動判別)
- `Kalodata_Video_*.xlsx` ×1〜2 (2つある場合は行数が多い方が通常動画)

翌週は古いファイルを削除して新しいエクスポートに置き換えること。
