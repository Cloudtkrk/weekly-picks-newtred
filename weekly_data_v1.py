#!/usr/bin/env python3
"""
TikTok Shop 週次おすすめ商品データ v1 (スコアリングなし版)
条件フィルタ + タグ付け + 売上順で整理して Excel / Discordテキストを出力
"""
import argparse
import datetime as dt
import sys

import os

import pandas as pd
import requests

sys.path.insert(0, ".")
from weekly_picks import (load_videos, load_products, tag_and_filter,
                          fmt_money, CONFIG)


def build_table(prod: pd.DataFrame, videos: pd.DataFrame) -> pd.DataFrame:
    """商品×直近7日動画実績を突合して表示用テーブルを作る"""
    vc = ["recent_video_gmv_7d", "n_videos_7d", "n_new_posts",
          "median_gpm", "organic_gmv_share"]
    df = prod.merge(videos[["product_key"] + vc], on="product_key", how="left")
    df[vc] = df[vc].fillna(0)

    def tags(r):
        t = []
        if r["is_campaign"]: t.append("🎫キャンペーン中")
        if r["is_seasonal"]: t.append("季節")
        if r["is_yakki"]: t.append("薬機法注意")
        if r["live_share"] >= 0.6: t.append("LIVE向き")
        elif r["live_share"] <= 0.2: t.append("動画向き")
        if r["recent_video_gmv_7d"] > 0 and r["organic_gmv_share"] >= 0.7:
            t.append("オーガニック")
        elif r["recent_video_gmv_7d"] > 0 and r["organic_gmv_share"] <= 0.3:
            t.append("広告主導")
        return "・".join(t)

    out = pd.DataFrame({
        "おすすめ": (df["recent_video_gmv_7d"] > 0).map({True: "⭐", False: ""}),
        "商品名": df["product_name"].str.slice(0, 50),
        "大分類": df["category"].astype(str).str.split(">").str[0].str.strip(),
        "カテゴリ": df["category"].astype(str).str.split(">").str[-1].str.strip(),
        "30日売上": df["gmv_30d"].map(fmt_money),
        "成長率": df["growth_pct"].map(lambda v: f"{v:+.0f}%"),
        "直近7日動画売上": df["recent_video_gmv_7d"].map(fmt_money),
        "直近7日動画本数": df["n_videos_7d"].astype(int),
        "販売件数": df["units"].astype(int).map(lambda v: f"{v/10000:.1f}万件" if v >= 10000 else f"{v:,}件"),
        "単価": df["avg_price"].map(fmt_money),
        "報酬目安/件": (df["avg_price"] * df["commission_pct"] / 100).map(
            lambda v: f"約{v:,.0f}円" if v > 0 else "-"),
        "報酬率": df["commission_pct"].map(lambda v: f"{v:.0f}%" if v else "-"),
        "参画クリエイター数": df["n_creators"].astype(int),
        "成立率": df["creator_cvr_pct"].map(lambda v: f"{v:.0f}%"),
        "評価": df["rating"],
        "タグ": df.apply(tags, axis=1),
        "掲載日": df["listed_at"].dt.strftime("%Y-%m-%d"),
        "商品リンク": df["tiktok_link"],
        "画像": df["image_link"],
        "画像alt": df["image_link_alt"],
        "_gmv": df["gmv_30d"],
        "_growth": df["growth_pct"],
        "_listed": df["listed_at"],
    })
    return out


# ============================================================
# Excel画像埋め込み
# ============================================================
IMG_CACHE = ".img_cache"
THUMB_PX = 72          # サムネイル一辺 (px)
ROW_PT = 58            # 行高 (pt) ≒ 76px

def _fetch_thumb(url: str) -> str | None:
    """画像をDL→サムネイル化してキャッシュ。失敗時None"""
    import hashlib
    from PIL import Image as PILImage
    os.makedirs(IMG_CACHE, exist_ok=True)
    key = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(IMG_CACHE, f"{key}.png")
    if os.path.exists(path):
        return path
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
        "Accept": "image/webp,image/png,image/*,*/*;q=0.8",
        "Referer": "https://www.kalodata.com/",
    }
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        if "image" not in r.headers.get("Content-Type", ""):
            raise ValueError(f"not an image: {r.headers.get('Content-Type')}")
        from io import BytesIO
        im = PILImage.open(BytesIO(r.content)).convert("RGB")
        im.thumbnail((THUMB_PX, THUMB_PX))
        im.save(path, "PNG")
        return path
    except Exception as e:
        print(f"[warn] 画像取得失敗: {url[:60]}... ({e})")
        return None


def embed_images(xlsx_path: str, sheet_names: list[str]):
    """各シートの「画像」列(URL)を実画像に置き換えて埋め込む"""
    from openpyxl import load_workbook
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.utils import get_column_letter

    wb = load_workbook(xlsx_path)
    for sn in sheet_names:
        if sn not in wb.sheetnames:
            continue
        ws = wb[sn]
        headers = {c.value: i + 1 for i, c in enumerate(ws[1])}
        img_col = headers.get("画像")
        if not img_col:
            continue
        col_letter = get_column_letter(img_col)
        ws.column_dimensions[col_letter].width = 11
        n_ok = 0
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=img_col)
            url = cell.value
            if not (isinstance(url, str) and url.startswith("http")):
                continue
            path = _fetch_thumb(url)
            if not path:
                alt_col = headers.get("画像alt")
                alt = ws.cell(row=row, column=alt_col).value if alt_col else None
                if isinstance(alt, str) and alt.startswith("http") and alt != url:
                    path = _fetch_thumb(alt)
            if path:
                cell.value = None      # 取得成功時のみURLを消して画像に置き換え
                img = XLImage(path)
                img.anchor = f"{col_letter}{row}"
                ws.add_image(img)
                ws.row_dimensions[row].height = ROW_PT
                n_ok += 1
            # 失敗時はURLをそのまま残す (クリックで画像を開ける)
        print(f"[info] {sn}: 画像 {n_ok}件 埋め込み")
    wb.save(xlsx_path)


def make_embed(r, kind: str) -> dict:
    color = 0xE74C3C if kind == "hot" else 0x2ECC71
    desc = []
    if kind == "hot":
        desc.append(f"30日売上 **{r['30日売上']}**（{r['販売件数']}）")
    else:
        desc.append(f"成長率 **{r['成長率']}**｜30日売上 **{r['30日売上']}**｜掲載 {r['掲載日']}")
    desc.append(f"単価 {r['単価']}｜報酬率※ **{r['報酬率']}**→1件 **{r['報酬目安/件']}**｜成立率 {r['成立率']}（参画{r['参画クリエイター数']}人）")
    if r["タグ"]:
        desc.append(f"🏷️ {r['タグ']}")
    star = "⭐ " if r.get("おすすめ") == "⭐" and kind == "hot" else ""
    embed = {
        "title": (star + str(r["商品名"]))[:100],
        "url": r["商品リンク"] if isinstance(r["商品リンク"], str) and r["商品リンク"].startswith("http") else None,
        "description": "\n".join(desc),
        "color": color,
        "footer": {"text": r["カテゴリ"]},
    }
    if isinstance(r["画像"], str) and r["画像"].startswith("http"):
        embed["thumbnail"] = {"url": r["画像"]}
    return {k: v for k, v in embed.items() if v is not None}


def post_discord_embeds(hot, new_tbl, webhook, top_per_cat):
    def send(content=None, embeds=None):
        payload = {}
        if content: payload["content"] = content
        if embeds: payload["embeds"] = embeds
        requests.post(webhook, json=payload, timeout=15).raise_for_status()

    today = dt.date.today().strftime("%m/%d")
    send(content=f"# 📦 今週のおすすめ商品（{today}更新）\n"
                 f"-# ※報酬率は取得時点の参考値です。実際の料率は各案件のアフィリエイトセンターで必ず確認してください")
    for label, tbl, kind in [("🔥 売れ筋", hot, "hot"), ("🚀 チャレンジ", new_tbl, "challenge")]:
        for cat, g in tbl.groupby("大分類", sort=False):
            g = g.head(top_per_cat)
            embeds = [make_embed(r, kind) for _, r in g.iterrows()]
            # Discordは1メッセージ10 embedまで
            for i in range(0, len(embeds), 10):
                head = f"## {label}｜▼ {cat}" if i == 0 else None
                send(content=head, embeds=embeds[i:i+10])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--videos", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--post", action="store_true", help="Discordにembed形式で投稿")
    ap.add_argument("--webhook", default=os.environ.get("DISCORD_WEBHOOK_URL", ""))
    ap.add_argument("--top-per-cat", type=int, default=5,
                    help="Discord投稿時の1カテゴリあたり上限件数")
    ap.add_argument("--images", action="store_true",
                    help="商品画像をダウンロードしてExcelに埋め込む")
    ap.add_argument("--html", action="store_true",
                    help="画像付きHTMLレポートも出力する")
    ap.add_argument("--html-embed", action="store_true",
                    help="画像をbase64でHTML内に埋め込む (どこで開いても表示される自己完結版)")
    ap.add_argument("--no-archive", action="store_true",
                    help="archive/<日付>/ スナップショットと data/<日付>.json を保存しない")
    args = ap.parse_args()

    videos = load_videos(args.videos)
    prod_main = tag_and_filter(load_products(args.products))
    prod_main = prod_main[prod_main["n_creators"] > CONFIG["hot_min_creators"]]  # 売れ筋のみ: 低参画=専売疑いを除外
    prod_new = tag_and_filter(load_products(args.new))
    # チャレンジ: 成長率マイナスと参画3人以下を除外
    prod_new = prod_new[(prod_new["growth_pct"] >= CONFIG["challenge_min_growth"])
                        & (prod_new["n_creators"] > CONFIG["challenge_min_creators"])]

    hot = build_table(prod_main, videos).sort_values("_gmv", ascending=False)
    # チャレンジ: 掲載45日以内(データにあれば適用) → 成長率順
    new_tbl = build_table(prod_new, videos)
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=45)
    recent_mask = new_tbl["_listed"] >= cutoff
    if recent_mask.any():
        new_tbl = new_tbl[recent_mask]
    new_tbl = new_tbl.sort_values("_growth", ascending=False)

    drop = ["_gmv", "_growth", "_listed"]
    hot_raw_gmv = hot["_gmv"]
    new_raw_gmv = new_tbl["_gmv"]
    hot = hot.drop(columns=drop)
    new_tbl = new_tbl.drop(columns=drop)

    # カテゴリサマリー (大分類ごとの件数と売上合計)
    def cat_summary(tbl, gmv_raw):
        s = tbl.copy()
        s["_g"] = gmv_raw.loc[s.index]
        agg = (s.groupby("大分類")
                .agg(商品数=("商品名", "count"), 合計30日売上=("_g", "sum"))
                .sort_values("合計30日売上", ascending=False))
        agg["合計30日売上"] = agg["合計30日売上"].map(fmt_money)
        return agg.reset_index()

    hot_gmv_raw = hot_raw_gmv
    new_gmv_raw = new_raw_gmv
    # 大分類を売上合計の大きい順に並べ、その中で商品を売上順に
    cat_order = (hot.assign(_g=hot_gmv_raw).groupby("大分類")["_g"].sum()
                    .sort_values(ascending=False).index.tolist())
    hot["_cat_rank"] = hot["大分類"].map({c: i for i, c in enumerate(cat_order)})
    hot = hot.sort_values(["_cat_rank"], kind="stable").drop(columns="_cat_rank")
    new_tbl = new_tbl.sort_values("大分類", kind="stable")

    out_path = args.out or f"weekly_data_{dt.date.today():%Y%m%d}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        cat_summary(hot, hot_gmv_raw).to_excel(w, sheet_name="カテゴリ別サマリー", index=False)
        hot.to_excel(w, sheet_name="売れ筋候補", index=False)
        new_tbl.to_excel(w, sheet_name="チャレンジ候補", index=False)
        # 列幅調整
        for ws in w.book.worksheets:
            for col_cells in ws.columns:
                width = max(len(str(c.value)) for c in col_cells if c.value) + 2
                ws.column_dimensions[col_cells[0].column_letter].width = min(width, 50)

    print(f"[info] 売れ筋候補 {len(hot)}件 / チャレンジ候補 {len(new_tbl)}件 → {out_path}")

    if args.images:
        embed_images(out_path, ["売れ筋候補", "チャレンジ候補"])

    if args.html or args.html_embed:
        from report_html import write_site, archive_site
        site_dir = "weekly_site"
        write_site(hot, new_tbl, site_dir, embed=args.html_embed)
        print(f"[info] Webサイト出力: {site_dir}/index.html (売れ筋), "
              f"{site_dir}/challenge.html (チャレンジ)"
              + (" [画像埋め込み版]" if args.html_embed else ""))
        if not args.no_archive:
            arch_dir = archive_site(hot, new_tbl, root_dir=".")
            print(f"[info] アーカイブ保存: {arch_dir}/ と data/*.json "
                  f"(archive/ data/ もコミット対象)")

    # Discordプレビュー (テキスト)
    today = dt.date.today().strftime("%m/%d")
    lines = [f"# 📦 今週のおすすめ商品データ（{today}）", "",
             "# 🔥 売れ筋候補"]
    for cat, g in hot.groupby("大分類", sort=False):
        lines += [f"## ▼ {cat}（{len(g)}件）"]
        for _, r in g.iterrows():
            lines += [
                f"**{r['商品名']}**（{r['カテゴリ']}）",
                f"　30日売上 {r['30日売上']}（{r['販売件数']}）｜直近7日動画売上 {r['直近7日動画売上']}（{r['直近7日動画本数']}本）",
                f"　単価 {r['単価']}｜報酬率 {r['報酬率']}→**1件{r['報酬目安/件']}**｜成立率 {r['成立率']}（参画{r['参画クリエイター数']}人）",
                f"　タグ: {r['タグ'] or 'なし'}", ""]
    lines += ["# 🚀 チャレンジ候補"]
    for cat, g in new_tbl.groupby("大分類", sort=False):
        lines += [f"## ▼ {cat}（{len(g)}件）"]
        for _, r in g.iterrows():
            lines += [
                f"**{r['商品名']}**（{r['カテゴリ']}）",
                f"　成長率 {r['成長率']}｜30日売上 {r['30日売上']}｜掲載日 {r['掲載日']}",
                f"　単価 {r['単価']}｜報酬率 {r['報酬率']}｜成立率 {r['成立率']}",
                f"　タグ: {r['タグ'] or 'なし'}", ""]
    print("\n" + "\n".join(lines))

    if args.post:
        if not args.webhook:
            sys.exit("[error] --webhook または DISCORD_WEBHOOK_URL を設定してください")
        post_discord_embeds(hot, new_tbl, args.webhook, args.top_per_cat)
        print("[info] Discordに投稿しました")


if __name__ == "__main__":
    main()
