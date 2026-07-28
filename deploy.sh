#!/bin/bash
# 週次レポートサイトを公開 (git push → Vercel自動デプロイ)
# 使い方: ./deploy.sh <weekly_siteフォルダ> <lp-collectionのローカルパス>
set -e
SITE="$1"
REPO="$2"
mkdir -p "$REPO/weekly"
cp "$SITE"/index.html "$SITE"/challenge.html "$REPO/weekly/"
cp "$SITE"/index.html "$REPO/weekly/$(date +%Y%m%d).html"   # アーカイブ
cd "$REPO"
git add weekly/
git commit -m "weekly picks $(date +%Y-%m-%d)"
git push
echo "✅ push完了 → https://<ドメイン>/weekly/ (売れ筋) と /weekly/challenge.html (チャレンジ)"
