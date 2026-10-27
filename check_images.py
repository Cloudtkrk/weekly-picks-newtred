"""公開前チェック: 画像なし (自社ホストのフォールバック=実在しない) のカードが無いか確認する。
使い方: python check_images.py [preview|.]   (既定 preview)
画像なしの商品IDを列挙し、1件でもあれば終了コード1。公開は0件になってから行う。"""
import re
import sys

d = sys.argv[1] if len(sys.argv) > 1 else "preview"
missing = {}
for f in ("index.html", "challenge.html"):
    s = open(f"{d}/{f}", encoding="utf-8").read()
    for pid in re.findall(r"product-images/(\d+)\.jpeg", s):
        missing.setdefault(pid, set()).add(f)
for pid, fs in sorted(missing.items()):
    print(pid, ",".join(sorted(fs)))
print(f"画像なし: {len(missing)}件")
sys.exit(1 if missing else 0)
