# weekly-picks

TikTok Shop クリエイター向け・週次おすすめ商品リスト生成ツール。
詳細な仕様と運用手順は `CLAUDE.md` を参照 (Claude Code がこれを読んで作業します)。

## セットアップ
```
pip install -r requirements.txt
```

## 使い方
1. Kalodataエクスポート3ファイルを `input/` に置く
2. Claude Code に「今週の生成して」と指示 (または手動で下記)
```
python weekly_data_v1.py --products input/<売れ筋>.xlsx --new input/<チャレンジ>.xlsx \
    --videos input/<動画>.xlsx --html
```
3. `weekly_site/` の2ファイルを GitHub (weekly-picks-newtred) にアップ → Vercel自動デプロイ
