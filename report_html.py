"""週次おすすめ商品のHTMLレポート生成 (画像はブラウザが直接読み込む)"""
import datetime as dt
import html as _h


CSS = """
:root{
  --ink:#17181c; --sub:#6b7080; --line:#e8e9ee; --bg:#f6f7f9; --card:#ffffff;
  --hot:#e8384f; --chal:#10a37f; --accent:#25f4ee; --tag-bg:#f0f1f5;
}
*{box-sizing:border-box; margin:0; padding:0}
body{font-family:"Hiragino Sans","Noto Sans JP",system-ui,sans-serif;
     background:var(--bg); color:var(--ink); font-size:14px; line-height:1.55}
.wrap{max-width:860px; margin:0 auto; padding:28px 16px 60px}
header{display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;
       border-bottom:3px solid var(--ink); padding-bottom:14px; margin-bottom:8px}
header h1{font-size:22px; font-weight:800; letter-spacing:.02em}
header .date{color:var(--sub); font-size:13px}
.counts{margin:10px 0 26px; color:var(--sub); font-size:13px}
.counts b{color:var(--ink)}
.section-h{display:flex; align-items:center; gap:10px; margin:34px 0 6px}
.section-h .bar{width:6px; height:22px; border-radius:3px}
.section-h h2{font-size:17px; font-weight:800}
.section-h .note{color:var(--sub); font-size:12px}
.cat{margin:18px 0 4px; font-size:13px; font-weight:700; color:var(--sub);
     text-transform:none; letter-spacing:.04em}
.cat b{color:var(--ink); font-size:14px}
.card{display:flex; gap:14px; background:var(--card); border:1px solid var(--line);
      border-radius:12px; padding:12px; margin:8px 0}
.card img{width:76px; height:76px; object-fit:cover; border-radius:8px;
          background:var(--tag-bg); flex-shrink:0}
.card .noimg{width:76px; height:76px; border-radius:8px; background:var(--tag-bg);
             display:flex; align-items:center; justify-content:center;
             color:var(--sub); font-size:11px; flex-shrink:0}
.body{min-width:0; flex:1}
.name{font-weight:700; font-size:14px; margin-bottom:4px; display:block;
      color:var(--ink); text-decoration:none; overflow:hidden;
      display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical}
.name:hover{text-decoration:underline}
.stats{color:var(--sub); font-size:12.5px; margin-bottom:2px}
.stats b{color:var(--ink); font-variant-numeric:tabular-nums}
.reward{color:var(--hot); font-weight:700}
.tags{margin-top:6px; display:flex; gap:6px; flex-wrap:wrap}
.tag{font-size:11px; padding:2px 8px; border-radius:99px; background:var(--tag-bg);
     color:var(--sub); font-weight:600}
.tag.camp{background:#fff3d6; color:#8a6100}
.tag.yakki{background:#ffe4e8; color:#a1233a}
.rec{display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:800;
     color:#fff; background:linear-gradient(90deg,#ff5f3d,#e8384f);
     padding:3px 10px; border-radius:99px; margin-bottom:5px}
.info{cursor:help; border-bottom:1px dotted var(--sub)}
footer{margin-top:44px; color:var(--sub); font-size:12px;
       border-top:1px solid var(--line); padding-top:14px}
.tabs{display:flex; gap:8px; margin:16px 0 4px}
.tab{padding:9px 18px; border-radius:10px; font-weight:800; font-size:14px;
     text-decoration:none; color:var(--sub); background:var(--card);
     border:1px solid var(--line)}
.tab.active{color:#fff; border-color:transparent}
.tab.active.hot{background:var(--hot)}
.tab.active.chal{background:var(--chal)}
.filters{display:flex; gap:6px; flex-wrap:wrap; margin:14px 0 6px;
         position:sticky; top:0; background:var(--bg); padding:10px 0; z-index:5}
.chip{padding:5px 12px; border-radius:99px; font-size:12.5px; font-weight:700;
      background:var(--card); border:1px solid var(--line); color:var(--sub);
      cursor:pointer; user-select:none}
.chip.on{background:var(--ink); color:#fff; border-color:var(--ink)}
.catgrp.hidden{display:none}
@media(max-width:520px){.card img,.card .noimg{width:60px;height:60px}}
"""


def _tag_html(tags: str) -> str:
    if not tags:
        return ""
    out = []
    for t in tags.split("・"):
        cls = "tag"
        if "キャンペーン" in t: cls += " camp"
        if "薬機法" in t: cls += " yakki"
        out.append(f'<span class="{cls}">{_h.escape(t)}</span>')
    return f'<div class="tags">{"".join(out)}</div>'


def _img_src(r, embed_fn=None) -> str:
    """embed_fn があれば base64 data URI、なければ通常URL"""
    url = r["画像"] if isinstance(r["画像"], str) and r["画像"].startswith("http") else ""
    if not url:
        return ""
    if embed_fn:
        b64 = embed_fn(url, r.get("画像alt", ""))
        return b64 or ""   # 取得失敗時は空 (no image表示)
    return url


def _card(r, kind: str, embed_fn=None) -> str:
    src_val = _img_src(r, embed_fn)
    if embed_fn:
        img = (f'<img src="{src_val}" alt="">' if src_val
               else '<div class="noimg">no image</div>')
    elif isinstance(r["画像"], str) and r["画像"].startswith("http"):
        alt = r.get("画像alt", "")
        alt_attr = _h.escape(alt) if isinstance(alt, str) and alt.startswith("http") else ""
        img = (f'<img src="{_h.escape(r["画像"])}" data-alt="{alt_attr}" loading="lazy" '
               f'referrerpolicy="no-referrer" alt="" '
               f"onerror=\"if(this.dataset.alt&&this.src!==this.dataset.alt)"
               f"{{this.src=this.dataset.alt}}else{{this.outerHTML="
               f"'<div class=noimg>no image</div>'}}\">")
    else:
        img = '<div class="noimg">no image</div>' 
    link = r["商品リンク"] if isinstance(r["商品リンク"], str) and r["商品リンク"].startswith("http") else "#"
    rec = ('<span class="rec">⭐ 今週売れてる</span><br>'
           if kind == "hot" and r.get("おすすめ") == "⭐" else "")
    if kind == "hot":
        line1 = f'30日売上 <b>{r["30日売上"]}</b>（{r["販売件数"]}）' 
    else:
        line1 = (f'成長率 <b>{r["成長率"]}</b>｜30日売上 <b>{r["30日売上"]}</b>'
                 f'（{r["販売件数"]}）｜掲載 {r["掲載日"]}')
    line2 = (f'単価 {r["単価"]}｜報酬率※ <b>{r["報酬率"]}</b>'
             f' → 1件 <span class="reward">{r["報酬目安/件"]}</span>｜'
             f'<span class="info" title="その商品に参画したクリエイターのうち、実際に売上を出した人の割合">成立率</span> '
             f'<b>{r["成立率"]}</b>（参画{r["参画クリエイター数"]}人）')
    return (f'<div class="card">{img}<div class="body">{rec}'
            f'<a class="name" href="{_h.escape(link)}" target="_blank">{_h.escape(str(r["商品名"]))}</a>'
            f'<div class="stats">{line1}</div><div class="stats">{line2}</div>'
            f'{_tag_html(r["タグ"])}</div></div>')


def _section(tbl, kind: str, embed_fn=None) -> str:
    parts = []
    for cat, g in tbl.groupby("大分類", sort=False):
        cat_e = _h.escape(str(cat))
        parts.append(f'<div class="catgrp" data-cat="{cat_e}">')
        parts.append(f'<div class="cat">▼ <b>{cat_e}</b>（{len(g)}件）</div>')
        parts += [_card(r, kind, embed_fn) for _, r in g.iterrows()]
        parts.append('</div>')
    return "\n".join(parts)


FILTER_JS = """
<script>
document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => {
  document.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
  c.classList.add('on');
  const v = c.dataset.cat;
  document.querySelectorAll('.catgrp').forEach(g =>
    g.classList.toggle('hidden', v !== 'all' && g.dataset.cat !== v));
}));
</script>"""


def _filter_bar(tbl) -> str:
    cats = list(dict.fromkeys(tbl["大分類"].astype(str)))
    chips = ['<span class="chip on" data-cat="all">すべて</span>']
    chips += [f'<span class="chip" data-cat="{_h.escape(c)}">{_h.escape(c)}</span>' for c in cats]
    return f'<div class="filters">{"".join(chips)}</div>' 


def make_embed_fn():
    """画像DL→72pxサムネ→base64 data URI 化 (失敗時None)"""
    import base64, hashlib, os
    from io import BytesIO
    import requests as rq
    from PIL import Image as PILImage
    os.makedirs(".img_cache", exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

    def fetch(url, alt=""):
        key = hashlib.md5(url.encode()).hexdigest()
        cpath = os.path.join(".img_cache", f"{key}.jpg")
        if not os.path.exists(cpath):
            ok = False
            for u in [url, alt]:
                if not (isinstance(u, str) and u.startswith("http")):
                    continue
                try:
                    r = rq.get(u, timeout=10, headers=headers)
                    r.raise_for_status()
                    im = PILImage.open(BytesIO(r.content)).convert("RGB")
                    im.thumbnail((144, 144))
                    im.save(cpath, "JPEG", quality=80)
                    ok = True
                    break
                except Exception:
                    continue
            if not ok:
                return None
        with open(cpath, "rb") as f:
            return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    return fetch


def _page(tbl, kind: str, out_path: str, embed_fn, today: str,
          n_hot: int, n_chal: int):
    if kind == "hot":
        title, color_cls = "🔥 売れ筋", "hot"
        tabs = (f'<a class="tab active hot" href="./">🔥 売れ筋（{n_hot}）</a>'
                f'<a class="tab" href="./challenge.html">🚀 チャレンジ（{n_chal}）</a>')
    else:
        title, color_cls = "🚀 チャレンジ", "chal"
        tabs = (f'<a class="tab" href="./">🔥 売れ筋（{n_hot}）</a>'
                f'<a class="tab active chal" href="./challenge.html">🚀 チャレンジ（{n_chal}）</a>')
    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} 週次おすすめ商品 {today}</title><style>{CSS}</style></head><body>
<div class="wrap">
<header><h1>📦 週次おすすめ商品</h1><span class="date">{today} 更新</span></header>
<div class="tabs">{tabs}</div>
{_filter_bar(tbl)}
{_section(tbl, kind, embed_fn)}
<footer>⭐ <b>今週売れてる</b>＝直近7日間に投稿動画から売上が発生している商品（今から乗っても売れやすい）<br>
<b>成立率</b>＝その商品に参画したクリエイターのうち、実際に売上を出した人の割合。高いほど「乗れば売れる」商品です<br><br>
※ 報酬率・1件あたり報酬目安は取得時点の<b>参考値</b>です。実際の料率・条件は必ず各案件のアフィリエイトセンターで確認してください。<br>
⚠️ 薬機法注意タグの商品は投稿前に表現チェック相談へ。売上等の数値は独自集計の参考値です。</footer>
</div>{FILTER_JS}</body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


def write_site(hot, new_tbl, out_dir: str, embed: bool = False):
    import os
    os.makedirs(out_dir, exist_ok=True)
    embed_fn = make_embed_fn() if embed else None
    today = dt.date.today().strftime("%Y/%m/%d")
    _page(hot, "hot", os.path.join(out_dir, "index.html"),
          embed_fn, today, len(hot), len(new_tbl))
    _page(new_tbl, "challenge", os.path.join(out_dir, "challenge.html"),
          embed_fn, today, len(hot), len(new_tbl))
