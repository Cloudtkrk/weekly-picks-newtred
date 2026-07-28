#!/usr/bin/env python3
"""
TikTok Shop 週次おすすめ商品リスト生成パイプライン
====================================================
入力 (Kalodataエクスポート3ファイル):
  1. products_main.xlsx   : 商品タブ / 過去30日 / アフィリ対応✔ / コミッション≥10% / 売上高順 上位150
  2. products_new.xlsx    : 商品タブ / 掲載日≤45日 / 成長率順 上位100
  3. videos_7d.xlsx       : 動画タブ / 過去7日 / 売上高順 上位200

出力:
  - weekly_picks_YYYYMMDD.xlsx (社内確認用)
  - Discord Webhook投稿 (--post フラグ指定時)

使い方:
  python weekly_picks.py --products products_main.xlsx --new products_new.xlsx \
      --videos videos_7d.xlsx [--post] [--webhook URL]
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata

import pandas as pd
import requests

# ============================================================
# 設定 (ここを調整して運用チューニング)
# ============================================================
CONFIG = {
    # --- 売れ筋の閾値 ---
    "hot_min_gmv": 5_000_000,         # 30日売上 500万円以上 (連携クリエイター経由・TTS日本の規模感)
    "hot_min_growth": -20.0,          # 成長率 -20%まで許容
    "hot_min_rating": 4.0,
    # --- チャレンジの閾値 ---
    "new_min_growth": 100.0,          # 成長率 +100%以上
    "new_gmv_range": (3_000_000, 30_000_000),  # 300万〜3,000万円
    "new_min_rating": 4.0,
    # --- 直近動画売上の判定 ---
    "recent_video_days": 7,           # 「新規投稿」とみなす日数
    # --- クリエイタープロデュース商品の除外名 (ここに追記して運用) ---
    "exclude_names": ["上司のあさみ"],
    # --- キャンペーンタグ用ワード (除外せずタグ付け) ---
    "campaign_words": ["クーポン", "OFF", "ＯＦＦ", "SALE", "セール", "割引", "福袋"],
    # --- 季節ワード (除外せずタグ付け) ---
    "seasonal_words": ["扇風機", "冷感", "冷風", "日傘", "UVカット", "ひんやり",
                       "クーラー", "ネッククーラー", "遮光"],
    # --- 薬機法注意カテゴリ ---
    "yakki_categories": ["フェイシャル美容機器", "スキンケア", "ヘアケア", "ボディケア",
                         "サプリメント", "健康食品", "美容機器"],
    # --- 出力件数 ---
    "n_hot": 10,
    "n_challenge": 5,
    # --- スコア重み ---
    "hot_weights": {"gmv": 0.25, "recent_video_gmv": 0.3, "gpm": 0.15,
                    "commission": 0.15, "creator_cvr": 0.15},
    "challenge_weights": {"growth": 0.4, "recent_video_gmv": 0.3,
                          "scarcity": 0.2, "commission": 0.1},
}

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


# ============================================================
# ユーティリティ
# ============================================================
def norm_name(s: str, length: int = 30) -> str:
    """商品名を突合キーに正規化: NFKC正規化 + 空白/記号除去 + 先頭N文字"""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\s\u3000【】\[\]()（）!！?？・、。,\.]", "", s)
    return s[:length]


def parse_money(v) -> float:
    """'5,294万円' '3,013万円' '¥1,234' などを円の数値に変換"""
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").replace("¥", "").replace("円", "").strip()
    # レンジ表記 "3133.00-7485.00" は中間値を採用
    rng = re.match(r"^([\d.]+)\s*-\s*([\d.]+)$", s)
    if rng:
        return (float(rng.group(1)) + float(rng.group(2))) / 2
    m = re.match(r"^([\d.]+)(億|万)?$", s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return 0.0
    val = float(m.group(1))
    unit = m.group(2)
    if unit == "億":
        val *= 100_000_000
    elif unit == "万":
        val *= 10_000
    return val


def parse_pct(v) -> float:
    """'-32.9%' '>999.9%' '335.3%' → float"""
    if pd.isna(v):
        return 0.0
    s = str(v).replace("%", "").replace(">", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def pct_rank(series: pd.Series) -> pd.Series:
    """0-100のパーセンタイルスコアに正規化"""
    if series.nunique() <= 1:
        return pd.Series(50.0, index=series.index)
    return series.rank(pct=True) * 100


def fix_image_url(u):
    """Kalodataエクスポートの不整合テンプレート resize-webp:...jpeg を修正
    → (jpeg統一版, webp統一版) を返す"""
    if not isinstance(u, str) or not u.startswith("http"):
        return "", ""
    if "-resize-webp:" in u and u.endswith(".jpeg"):
        return u.replace("-resize-webp:", "-resize-jpeg:"), u[:-5] + ".webp"
    return u, u


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """カラム名の揺れに対応した検索 (部分一致)"""
    for cand in candidates:
        for col in df.columns:
            if cand in str(col):
                return col
    return None


# ============================================================
# 1. 動画データの集計 (過去7日エクスポート)
# ============================================================
def load_videos(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0)
    col_product = find_col(df, ["商品名"])
    col_gmv = find_col(df, ["取引金額"])
    col_posted = find_col(df, ["投稿日"])
    col_gpm = find_col(df, ["1000視聴"])
    col_ad_ratio = find_col(df, ["広告視聴率"])
    col_views = find_col(df, ["視聴回数"])

    out = pd.DataFrame({
        "product_key": df[col_product].map(norm_name),
        "product_name": df[col_product],
        "video_gmv": df[col_gmv].map(parse_money),
        "posted_at": pd.to_datetime(df[col_posted], errors="coerce"),
        "gpm": pd.to_numeric(df[col_gpm], errors="coerce").fillna(0),
        "ad_ratio": df[col_ad_ratio].map(parse_pct),
        "views": pd.to_numeric(df[col_views], errors="coerce").fillna(0),
    })

    today = pd.Timestamp.now().normalize()
    recent_cut = today - pd.Timedelta(days=CONFIG["recent_video_days"])

    agg = out.groupby("product_key").apply(
        lambda g: pd.Series({
            "recent_video_gmv_7d": g["video_gmv"].sum(),          # 過去7日期間なので全て直近売上
            "n_videos_7d": len(g),
            "new_post_gmv": g.loc[g["posted_at"] >= recent_cut, "video_gmv"].sum(),
            "n_new_posts": (g["posted_at"] >= recent_cut).sum(),
            "median_gpm": g["gpm"].median(),
            "organic_gmv_share": (
                g.loc[g["ad_ratio"] < 20, "video_gmv"].sum() / g["video_gmv"].sum()
                if g["video_gmv"].sum() > 0 else 0
            ),
            "top_video_desc": g.sort_values("video_gmv", ascending=False)
                               ["product_name"].iloc[0],
        }),
        include_groups=False,
    ).reset_index()
    return agg


# ============================================================
# 2. 商品データの読み込み (商品タブエクスポート)
# ============================================================
def load_products(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0)
    col_name = find_col(df, ["商品名称", "商品名", "商品情報"])
    col_gmv = find_col(df, ["取引金額 (", "取引金額("])          # 合計GMV (平均/ライブ/動画と区別)
    col_gmv = "取引金額 (¥)" if "取引金額 (¥)" in df.columns else col_gmv
    col_growth = find_col(df, ["成長率"])
    col_units = find_col(df, ["販売数", "販売件数"])
    col_rating = find_col(df, ["商品レビュー", "商品評価", "評価"])
    col_price = find_col(df, ["平均取引金額", "価格(¥)", "価格 (¥)", "平均販売価格"])  # 実売単価を優先
    col_commission = find_col(df, ["報酬率", "コミッション"])
    col_creators = find_col(df, ["クリエイター数"])
    col_cvr = find_col(df, ["クリエイター取引成立率"])
    col_listed = find_col(df, ["アップロード時間", "掲載日"])
    col_category = find_col(df, ["カテゴリー", "カテゴリ"])
    col_live = find_col(df, ["ライブ取引金額"])
    col_video = find_col(df, ["動画取引金額"])
    col_tt_link = find_col(df, ["TikTokリンク"])
    col_kalo_link = find_col(df, ["Kalodata詳細リンク"])

    out = pd.DataFrame({
        "product_key": df[col_name].map(norm_name),
        "product_name": df[col_name],
        "gmv_30d": df[col_gmv].map(parse_money),
        "growth_pct": df[col_growth].map(parse_pct) if col_growth else 0.0,
        "units": pd.to_numeric(df[col_units], errors="coerce").fillna(0) if col_units else 0,
        "rating": pd.to_numeric(df[col_rating], errors="coerce").fillna(0) if col_rating else 0,
        "avg_price": df[col_price].map(parse_money) if col_price else 0.0,
        "commission_pct": df[col_commission].map(parse_pct) if col_commission else 0.0,
        "affiliate_ok": df[col_commission].astype(str).str.strip().ne("-") if col_commission else True,
        "n_creators": pd.to_numeric(df[col_creators], errors="coerce").fillna(0) if col_creators else 0,
        "creator_cvr_pct": df[col_cvr].map(parse_pct) if col_cvr else 0.0,
        "listed_at": pd.to_datetime(df[col_listed], errors="coerce") if col_listed else pd.NaT,
        "category": df[col_category] if col_category else "",
        "live_gmv": df[col_live].map(parse_money) if col_live else 0.0,
        "video_gmv_30d": df[col_video].map(parse_money) if col_video else 0.0,
        "tiktok_link": df[col_tt_link] if col_tt_link else "",
        "image_link": (df[find_col(df, ["画像リンク"])].map(lambda u: fix_image_url(u)[0])
                        if find_col(df, ["画像リンク"]) else ""),
        "image_link_alt": (df[find_col(df, ["画像リンク"])].map(lambda u: fix_image_url(u)[1])
                        if find_col(df, ["画像リンク"]) else ""),
        "kalodata_link": df[col_kalo_link] if col_kalo_link else "",
    })
    # チャネル構成比 (動画向き / LIVE向き判定用)
    content_gmv = out["live_gmv"] + out["video_gmv_30d"]
    out["live_share"] = (out["live_gmv"] / content_gmv).where(content_gmv > 0, 0)
    return out.drop_duplicates(subset="product_key")


# ============================================================
# 3. タグ付け & 除外
# ============================================================
def tag_and_filter(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    name = df["product_name"].fillna("")
    df["is_campaign"] = name.apply(
        lambda s: any(w in s for w in CONFIG["campaign_words"]))
    df["is_excluded"] = name.apply(
        lambda s: any(w in s for w in CONFIG["exclude_names"]))
    # クリエイター専売品 (人名+専用) の除外:
    #  「様/さん/ちゃん専用」は無条件、それ以外の「専用」は参画3人以下の場合のみ
    hard_ded = name.str.contains("様専用|さん専用|ちゃん専用", na=False)
    soft_ded = name.str.contains("専用", na=False) & (df["n_creators"] <= 10)
    df["is_excluded"] = df["is_excluded"] | hard_ded | soft_ded
    df["is_seasonal"] = name.apply(
        lambda s: any(w in s for w in CONFIG["seasonal_words"]))
    df["is_yakki"] = df["category"].fillna("").apply(
        lambda s: any(w in str(s) for w in CONFIG["yakki_categories"]))
    # アフィリ非対応 (報酬率 "-") はクリエイター向けリストから必ず除外
    return df[~df["is_excluded"] & df["affiliate_ok"]]


# ============================================================
# 4. スコアリング
# ============================================================
def score_hot(df: pd.DataFrame) -> pd.DataFrame:
    c = CONFIG
    d = df[
        (df["gmv_30d"] >= c["hot_min_gmv"])
        & (df["growth_pct"] >= c["hot_min_growth"])
        & (df["rating"] >= c["hot_min_rating"])
        & (df["recent_video_gmv_7d"] > 0)          # 直近7日に動画売上があること
    ].copy()
    w = c["hot_weights"]
    d["score"] = (
        w["gmv"] * pct_rank(d["gmv_30d"])
        + w["recent_video_gmv"] * pct_rank(d["recent_video_gmv_7d"])
        + w["gpm"] * pct_rank(d["median_gpm"])
        + w["commission"] * pct_rank(d["commission_pct"])
        + w["creator_cvr"] * pct_rank(d["creator_cvr_pct"])
    )
    return d.sort_values("score", ascending=False).head(c["n_hot"])


def score_challenge(df: pd.DataFrame) -> pd.DataFrame:
    c = CONFIG
    lo, hi = c["new_gmv_range"]
    d = df[
        (df["growth_pct"] >= c["new_min_growth"])
        & (df["gmv_30d"].between(lo, hi))
        & (df["rating"] >= c["new_min_rating"])
    ].copy()
    w = c["challenge_weights"]
    d["scarcity"] = 1 / (1 + d["n_creators"])
    d["score"] = (
        w["growth"] * pct_rank(d["growth_pct"])
        + w["recent_video_gmv"] * pct_rank(d["recent_video_gmv_7d"])
        + w["scarcity"] * pct_rank(d["scarcity"])
        + w["commission"] * pct_rank(d["commission_pct"])
    )
    return d.sort_values("score", ascending=False).head(c["n_challenge"])


# ============================================================
# 5. Discord メッセージ生成
# ============================================================
def fmt_money(v: float) -> str:
    if v >= 100_000_000:
        return f"{v/100_000_000:.1f}億円"
    if v >= 10_000:
        return f"{v/10_000:,.0f}万円"
    return f"{v:,.0f}円"


def product_line(row: pd.Series, rank: int, kind: str) -> str:
    tags = []
    if row.get("is_seasonal"):
        tags.append("🌡️季節商品")
    if row.get("is_yakki"):
        tags.append("⚠️薬機法注意")
    if row.get("organic_gmv_share", 0) >= 0.7:
        tags.append("🌱オーガニック向き")
    elif row.get("organic_gmv_share", 1) <= 0.3 and row.get("recent_video_gmv_7d", 0) > 0:
        tags.append("📢広告主導型")
    if row.get("live_share", 0) >= 0.6:
        tags.append("📺LIVE向き")
    elif row.get("live_share", 1) <= 0.2:
        tags.append("🎥動画向き")
    tag_str = " ".join(tags)

    emoji = "🔥" if kind == "hot" else "🚀"
    lines = [
        f"{emoji} **#{rank}｜{str(row['product_name'])[:40]}**",
        f"　30日売上 {fmt_money(row['gmv_30d'])}｜単価 {fmt_money(row['avg_price'])}"
        + (f"｜コミッション {row['commission_pct']:.0f}%" if row["commission_pct"] else ""),
        f"　📈 直近7日の動画売上 {fmt_money(row['recent_video_gmv_7d'])}"
        f"（動画{int(row['n_videos_7d'])}本 / うち新規投稿{int(row['n_new_posts'])}本）",
        f"　🎯 クリエイター成立率 {row['creator_cvr_pct']:.0f}%（参画{int(row['n_creators'])}人中）",
    ]
    if kind == "challenge":
        lines.append(f"　💡 成長率 {row['growth_pct']:+.0f}%（先行者チャンス）")
    if tag_str:
        lines.append(f"　{tag_str}")
    if isinstance(row.get("tiktok_link"), str) and row["tiktok_link"].startswith("http"):
        lines.append(f"　🔗 <{row['tiktok_link']}>")
    return "\n".join(lines)


def build_discord_message(hot: pd.DataFrame, challenge: pd.DataFrame) -> str:
    today = dt.date.today().strftime("%m/%d")
    parts = [f"# 📦 今週のおすすめ商品（{today}更新）",
             "",
             "## 🔥 売れ筋商品（実績あり・今週も動画で売れている）"]
    for i, (_, row) in enumerate(hot.iterrows(), 1):
        parts.append(product_line(row, i, "hot"))
        parts.append("")
    parts.append("## 🚀 チャレンジ商品（伸び始め・先行者チャンス）")
    for i, (_, row) in enumerate(challenge.iterrows(), 1):
        parts.append(product_line(row, i, "challenge"))
        parts.append("")
    parts.append("-# データ: Kalodata 過去30日 + 直近7日動画実績。⚠️付き商品は訴求表現に注意（担当に確認）")
    return "\n".join(parts)


def post_discord(content: str, webhook: str):
    # Discordは2000文字制限があるので分割投稿
    chunks, buf = [], ""
    for line in content.split("\n"):
        if len(buf) + len(line) + 1 > 1900:
            chunks.append(buf)
            buf = ""
        buf += line + "\n"
    if buf:
        chunks.append(buf)
    for chunk in chunks:
        r = requests.post(webhook, json={"content": chunk}, timeout=15)
        r.raise_for_status()


# ============================================================
# main
# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", required=True, help="商品タブ(30日)エクスポート")
    ap.add_argument("--new", required=True, help="商品タブ(新着)エクスポート")
    ap.add_argument("--videos", required=True, help="動画タブ(過去7日)エクスポート")
    ap.add_argument("--post", action="store_true", help="Discordに投稿する")
    ap.add_argument("--webhook", default=DISCORD_WEBHOOK)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    videos = load_videos(args.videos)
    prod_main = tag_and_filter(load_products(args.products))
    prod_new = tag_and_filter(load_products(args.new))

    # 突合: 商品名の正規化キーで動画実績を紐付け
    video_cols = ["recent_video_gmv_7d", "n_videos_7d", "new_post_gmv",
                  "n_new_posts", "median_gpm", "organic_gmv_share"]
    prod_main = prod_main.merge(videos.drop(columns=["top_video_desc"]),
                                on="product_key", how="left")
    prod_new = prod_new.merge(videos.drop(columns=["top_video_desc"]),
                              on="product_key", how="left")
    for df in (prod_main, prod_new):
        df[video_cols] = df[video_cols].fillna(0)

    hot = score_hot(prod_main)
    challenge = score_challenge(prod_new)
    # 重複排除: 売れ筋に入った商品はチャレンジから除外
    challenge = challenge[~challenge["product_key"].isin(hot["product_key"])]

    # 突合率レポート (商品名マッチの健全性チェック)
    match_rate = (prod_main["recent_video_gmv_7d"] > 0).mean()
    print(f"[info] 売れ筋母集団 {len(prod_main)}件 / 動画突合率 {match_rate:.0%}")
    print(f"[info] 売れ筋 {len(hot)}件 / チャレンジ {len(challenge)}件 選出")

    # Excel出力 (社内確認用)
    out_path = args.out or f"weekly_picks_{dt.date.today():%Y%m%d}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        hot.to_excel(w, sheet_name="売れ筋", index=False)
        challenge.to_excel(w, sheet_name="チャレンジ", index=False)
        prod_main.to_excel(w, sheet_name="母集団_売れ筋", index=False)
        prod_new.to_excel(w, sheet_name="母集団_新着", index=False)
    print(f"[info] 出力: {out_path}")

    msg = build_discord_message(hot, challenge)
    print("\n" + "=" * 60 + "\n" + msg)

    if args.post:
        if not args.webhook:
            sys.exit("[error] --webhook または環境変数 DISCORD_WEBHOOK_URL を設定してください")
        post_discord(msg, args.webhook)
        print("[info] Discordに投稿しました")


if __name__ == "__main__":
    main()
