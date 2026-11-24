"""🚀新商品タブの元データ: Googleスプレッドシート「商品選定リスト（クリエイター共有用）」(2026-11-24〜 ユーザー指示)

シートは7ジャンル×「｜新商品」(直近30日・掲載30日以内)「｜売上」(直近7日)の14タブ。
選定はシート側で済んでいるので、ここでは足切り・並べ替えをせずそのまま載せる。
報酬率はシートに無いので出さない (Kalodata でも読まない。ユーザー指示)。
売れ筋との重複は今までどおり除かない。

使い方 (ローカルで。Actions はシートを読まない):
  python sheet_new.py fetch            # 14タブを CSV で取り、input/Sheet_New_<YYYYMMDD>.csv に書く
  python sheet_new.py images           # 画像の無い商品だけ Kalodata の cover を product-images/kalodata/ に置く
生成側 (weekly_data_v1.py) は input/Sheet_New_*.csv があれば load_sheet_new() で🚀新商品にする。
"""
import csv
import datetime as dt
import glob
import io
import json
import os
import re
import sys
import time
import urllib.request

SHEET_ID = "1xrA6mAWH1AQsHQQbL98HjfAtIX8yPen4BinpwykuPHw"
# シート名の左側 → サイトのジャンル
GENRE = {
    "食品・飲料": "食品",
    "ガジェット家電": "家電ガジェット",
    "ホームリビング": "キッチン・ホーム用品",
    "キッチン・バス": "キッチン・ホーム用品",
    "アパレル": "アパレル",
    "ベビー・キッズ": "ベビー・キッズ",
    "美容": "美容",
}
N_TABS = 14          # gid 0〜13
COLS = ["商品ID", "商品名", "ジャンル", "元シート", "種類", "順位", "価格", "動画売上",
        "期間", "注文数", "成長率", "クリエイター数", "掲載日", "商品リンク"]
HERE = os.path.dirname(os.path.abspath(__file__))


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def read_tab(gid: int) -> list[dict]:
    """1タブ分。1行目=シート名、5行目=見出し、6行目から商品"""
    text = _get(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}").decode("utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    title = rows[0][0].strip()
    left, _, kind = title.partition("｜")
    if left not in GENRE or kind not in ("新商品", "売上"):
        sys.exit(f"[error] gid={gid} のシート名「{title}」が想定外です (ジャンル｜新商品/売上)")
    head_i = next((i for i, r in enumerate(rows) if r and r[0].strip() == "順位"), None)
    if head_i is None:
        sys.exit(f"[error] {title}: 見出し行 (順位…) がありません")
    head = [h.strip() for h in rows[head_i]]

    def col(prefix):
        for i, h in enumerate(head):
            if h.startswith(prefix):
                return i
        sys.exit(f"[error] {title}: 列「{prefix}…」がありません (見出し: {head})")

    c = {k: col(k) for k in ("順位", "商品名", "価格", "動画売上", "成長率", "クリエイター数", "掲載日", "TikTok商品URL")}
    c_orders = next(i for i, h in enumerate(head) if "注文数" in h)
    period = re.search(r"\((\d+日)\)", head[c["動画売上"]])
    out = []
    for r in rows[head_i + 1:]:
        if len(r) <= c["TikTok商品URL"] or not r[c["順位"]].strip():
            continue
        url = r[c["TikTok商品URL"]].strip()
        m = re.search(r"/product/(\d+)", url)
        if not m:
            continue
        out.append({
            "商品ID": m.group(1), "商品名": r[c["商品名"]].strip(), "ジャンル": GENRE[left],
            "元シート": title, "種類": kind, "順位": int(r[c["順位"]]),
            "価格": r[c["価格"]].strip(), "動画売上": r[c["動画売上"]].strip(),
            "期間": period.group(1) if period else "",
            "注文数": r[c_orders].strip(), "成長率": r[c["成長率"]].strip(),
            "クリエイター数": r[c["クリエイター数"]].strip(), "掲載日": r[c["掲載日"]].strip(),
            "商品リンク": f"https://shop.tiktok.com/view/product/{m.group(1)}?region=JP&locale=ja-JP",
        })
    return out


def fetch(day: str):
    rows, seen = [], {}
    for gid in range(N_TABS):
        tab = read_tab(gid)
        print(f"{tab[0]['元シート'] if tab else gid}: {len(tab)}件")
        rows += tab
        time.sleep(1)
    # 同じ商品が「｜新商品」と「｜売上」の両方にあれば1件にする (新商品側を残し、売上側の情報を足す)
    out = []
    for r in sorted(rows, key=lambda r: 0 if r["種類"] == "新商品" else 1):
        if r["商品ID"] in seen:
            seen[r["商品ID"]]["種類"] = "新商品・売上"
            continue
        seen[r["商品ID"]] = r
        out.append(r)
    path = os.path.join(HERE, "input", f"Sheet_New_{day}.csv")
    for old in glob.glob(os.path.join(HERE, "input", "Sheet_New_*.csv")):
        if old != path:
            os.remove(old)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"合計 {len(rows)}行 → 重複を除いて {len(out)}商品 → {os.path.relpath(path, HERE)}")


def latest_csv(input_dir: str) -> str | None:
    hits = sorted(glob.glob(os.path.join(input_dir, "Sheet_New_*.csv")))
    return hits[-1] if hits else None


def load_sheet_new(path: str, columns: list[str]):
    """サイトの新商品テーブル (売れ筋と同じ列) にする。並びは ジャンル順 → 新商品シート → 売上シート、各シートの順位"""
    import pandas as pd
    from weekly_picks import CONFIG, mapped_product_image, product_image_url
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = []
    for _, r in df.iterrows():
        link = r["商品リンク"]
        img = mapped_product_image(link) or product_image_url(link)
        if r["種類"] == "売上":
            tag = f"直近7日 注文{r['注文数']}件"
        elif r["種類"] == "新商品・売上":
            tag = f"掲載30日以内・直近7日も好調"
        else:
            tag = "掲載30日以内"
        rows.append({
            "おすすめ": "", "バッジ": "", "商品名": r["商品名"][:50], "ジャンル": r["ジャンル"],
            "大分類": r["元シート"], "カテゴリ": r["元シート"],
            "30日売上": r["動画売上"], "売上ラベル": f"動画売上({r['期間']})",
            "成長率": r["成長率"], "単価": r["価格"], "報酬率": "-",
            "参画クリエイター数": r["クリエイター数"], "タグ": tag,
            "掲載日": r["掲載日"].replace("/", "-"), "商品リンク": link, "商品ID": r["商品ID"],
            "動画URL": "", "動画投稿者": "", "動画売上": "", "動画再生数": "", "再現ガイド": "",
            "枠": "シート", "画像": img, "画像alt": "",
            "_g": CONFIG["genre_order"].index(r["ジャンル"]) if r["ジャンル"] in CONFIG["genre_order"] else 99,
            "_k": 0 if r["種類"].startswith("新商品") else 1, "_r": int(r["順位"]),
        })
    t = pd.DataFrame(rows).sort_values(["_g", "_k", "_r"], kind="stable").drop(columns=["_g", "_k", "_r"])
    for c in columns:
        if c not in t.columns:
            t[c] = "-"
    return t.reset_index(drop=True)


def images(input_dir: str):
    """画像の無い商品だけ img.kalocdn.com/tiktok.product/<ID>/cover.png を置く (ログイン不要のCDN。CLAUDE.md「商品画像」)"""
    path = latest_csv(input_dir)
    if not path:
        sys.exit("[error] input/Sheet_New_*.csv がありません。先に fetch")
    jpath = os.path.join(HERE, "product_images.json")
    with open(jpath, encoding="utf-8") as f:
        mapping = json.load(f)
    with open(path, encoding="utf-8") as f:
        ids = [r["商品ID"] for r in csv.DictReader(f)]
    # product-images/<ID>.jpeg (TAP用) があっても、公開前チェック (check_images.py) は「画像なし」と数えるので置く
    todo = [i for i in ids if i not in mapping]
    print(f"画像なし {len(todo)}件 / {len(ids)}件")
    os.makedirs(os.path.join(HERE, "product-images", "kalodata"), exist_ok=True)
    ng = []
    for pid in todo:
        try:
            b = _get(f"https://img.kalocdn.com/tiktok.product/{pid}/cover.png")
        except Exception as e:
            ng.append(pid); print(f"NG {pid}: {e}"); continue
        ext = ("jpg" if b[:3] == b"\xff\xd8\xff" else "png" if b[:8] == b"\x89PNG\r\n\x1a\n"
               else "webp" if b[8:12] == b"WEBP" else "")
        if not ext:
            ng.append(pid); print(f"NG {pid}: 画像ではない"); continue
        rel = f"product-images/kalodata/{pid}.{ext}"
        with open(os.path.join(HERE, rel), "wb") as f:
            f.write(b)
        mapping[pid] = "/" + rel
        time.sleep(0.5)
    with open(jpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(mapping, ensure_ascii=False, indent=0))   # 今までの書式のまま (字下げなし・末尾改行なし)
    print(f"追加 {len(todo) - len(ng)}件 / 取れなかった {len(ng)}件" + (f": {' '.join(ng)}" if ng else ""))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch(sys.argv[2] if len(sys.argv) > 2 else dt.date.today().strftime("%Y%m%d"))
    elif cmd == "images":
        images(os.path.join(HERE, "input"))
    else:
        print(__doc__)
