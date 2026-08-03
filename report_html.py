"""週次おすすめ商品のHTMLレポート生成 (画像はブラウザが直接読み込む)"""
import datetime as dt
import html as _h

from weekly_picks import CONFIG


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
     padding:3px 10px; border-radius:99px}
.pills{display:flex; gap:6px; flex-wrap:wrap; margin-bottom:5px}
.pill{display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:800;
      padding:3px 10px; border-radius:99px}
.pill.easy{background:#dcf5e5; color:#116932}
.pill.gem{background:#ede4fd; color:#5b21b6}
.pill.own{background:#ffe8d2; color:#9a3412}
.guide{background:var(--card); border:1px solid var(--line); border-radius:12px;
       padding:12px 14px; margin:12px 0 4px; font-size:12.5px; color:var(--sub)}
.guide .g-title{font-weight:800; font-size:13.5px; margin-bottom:8px; color:var(--ink)}
.guide ul{list-style:none; display:flex; flex-direction:column; gap:7px}
.guide li{display:flex; align-items:baseline; gap:8px; flex-wrap:wrap}
.info{cursor:help; border-bottom:1px dotted var(--sub)}
footer{margin-top:44px; color:var(--sub); font-size:12px;
       border-top:1px solid var(--line); padding-top:14px}
.tabs{display:flex; gap:8px; margin:16px 0 4px; overflow-x:auto;
      scrollbar-width:none; -webkit-overflow-scrolling:touch}
.tabs::-webkit-scrollbar{display:none}
.tab{white-space:nowrap; flex-shrink:0}
.tab{padding:9px 18px; border-radius:10px; font-weight:800; font-size:14px;
     text-decoration:none; color:var(--sub); background:var(--card);
     border:1px solid var(--line)}
.tab.active{color:#fff; border-color:transparent}
.tab.active.hot{background:var(--hot)}
.tab.active.chal{background:var(--chal)}
.tab.active.own{background:#f97316}
.tab.active.live{background:#7c3aed}
.pill.live{background:#ede9fe; color:#5b21b6}
.pill.feat{background:#fee2e2; color:#b91c1c}
.shop-h{display:flex; align-items:baseline; justify-content:space-between; gap:8px;
        margin:20px 0 4px; padding-top:6px; border-top:1px solid var(--line)}
.shop-name{font-weight:800; font-size:14.5px}
.shop-n{color:var(--sub); font-size:12px; white-space:nowrap}
.shoplink{color:var(--sub); text-decoration:none; border-bottom:1px dotted var(--sub)}
.shoplink:hover{color:var(--ink)}
.more{display:block; text-align:center; padding:10px; margin:6px 0 4px;
      background:var(--card); border:1px solid var(--line); border-radius:10px;
      font-size:12.5px; font-weight:700; color:var(--own-ink); text-decoration:none}
.more:hover{border-color:var(--own)}
.more.back{margin:10px 0 0; color:var(--sub)}
.filters{display:flex; gap:6px; flex-wrap:wrap; margin:14px 0 6px;
         position:sticky; top:0; background:var(--bg); padding:10px 0; z-index:5}
.chip{padding:5px 12px; border-radius:99px; font-size:12.5px; font-weight:700;
      background:var(--card); border:1px solid var(--line); color:var(--sub);
      cursor:pointer; user-select:none}
.chip.on{background:var(--ink); color:#fff; border-color:var(--ink)}
.catgrp.hidden{display:none}
.tab.arch{font-size:12.5px; padding:9px 12px}
.arch-note{margin:10px 0 0; padding:10px 12px; background:#fff3d6; color:#8a6100;
           border-radius:10px; font-size:12.5px}
.arch-note a{color:inherit; font-weight:700}
@media(max-width:640px){
  /* スマホ: カテゴリ選択チップを折り返さず横スクロール1行に (画面を占有しない) */
  .filters{flex-wrap:nowrap; overflow-x:auto; -webkit-overflow-scrolling:touch;
           scrollbar-width:none; margin-left:-16px; margin-right:-16px;
           padding-left:16px; padding-right:16px}
  .filters::-webkit-scrollbar{display:none}
  .chip{white-space:nowrap; flex-shrink:0}
}
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
    # 商品名の上のピル行: ⭐今週売れてる + サンプル承認難易度バッジ (併記可)
    pills = []
    if kind == "hot" and r.get("おすすめ") == "⭐":
        pills.append('<span class="rec">⭐ 今週売れてる</span>')
    for b in str(r.get("バッジ") or "").split("・"):
        if not b:
            continue
        cls = "easy" if b.startswith("🔰") else "gem" if b.startswith("💎") else "own"
        pills.append(f'<span class="pill {cls}">{_h.escape(b)}</span>')
    rec = f'<div class="pills">{"".join(pills)}</div>' if pills else ""
    # 表示はシンプルに3項目のみ。詳細指標はExcel/data JSON側に残す
    line1 = (f'30日売上 <b>{r["30日売上"]}</b>｜単価 {r["単価"]}｜'
             f'報酬率※ <b class="reward">{r["報酬率"]}</b>')
    return (f'<div class="card">{img}<div class="body">{rec}'
            f'<a class="name" href="{_h.escape(link)}" target="_blank">{_h.escape(str(r["商品名"]))}</a>'
            f'<div class="stats">{line1}</div>'
            f'{_tag_html(r["タグ"])}</div></div>')


def _section(tbl, kind: str, embed_fn=None) -> str:
    parts = []
    for cat, g in tbl.groupby("ジャンル", sort=False):
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
    cats = list(dict.fromkeys(tbl["ジャンル"].astype(str)))
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
          n_hot: int, n_chal: int, n_own: int = 0, n_live: int = 0):
    if kind == "hot":
        title, color_cls = "🔥 売れ筋", "hot"
        tabs = (f'<a class="tab active hot" href="./">🔥 売れ筋（{n_hot}）</a>'
                f'<a class="tab" href="./challenge.html">🚀 新商品（{n_chal}）</a>')
    else:
        title, color_cls = "🚀 新商品", "chal"
        tabs = (f'<a class="tab" href="./">🔥 売れ筋（{n_hot}）</a>'
                f'<a class="tab active chal" href="./challenge.html">🚀 新商品（{n_chal}）</a>')
    if n_own:
        tabs += f'<a class="tab" href="./recommend.html">🎁 おすすめ（{n_own}）</a>'
    if n_live:
        tabs += f'<a class="tab" href="./live.html">📺 ライブ（{n_live}）</a>'
    tabs += '<a class="tab arch" href="./archive/">📅 アーカイブ</a>'
    guide = ""
    if kind == "hot":
        guide = """<div class="guide"><div class="g-title">自分に合う商品の選び方</div><ul>
<li><span class="pill easy">🔰 初心者でも狙いやすい</span>承認ペースが速く成立率も高い、またはフォロワーの少ないクリエイターでも売れている実績あり</li>
<li><span class="pill own">🎁 自社サンプル可</span>弊社経由でサンプルを渡せる商品。実績ゼロでもまずここから</li>
<li><span class="pill gem">💎 狙い目</span>1人あたりの取り分が大きいが、承認には実績や投稿数が必要</li>
<li><span class="rec">⭐ 今週売れてる</span>直近7日も動画で売れている＝今から乗っても間に合う</li>
</ul></div>"""
    c = CONFIG
    badge_note = (
        f'🔰 <b>初心者でも狙いやすい</b>＝参画ペース{c["easy_pace"]}人/月以上 × '
        f'成立率{c["easy_cvr"]}%以上 × ⭐今週売れてる、'
        f'またはフォロワーの少ないクリエイターの動画で直近7日に売上実績あり ／ '
        f'💎 <b>狙い目（実績者向け）</b>＝1人あたりGMV{c["gem_gmv_per_creator"] // 10000}万円以上 × '
        f'成立率{c["gem_cvr"]}%以上 ／ '
        f'🎁 <b>自社サンプル可</b>＝弊社取扱ブランドの商品<br>'
        f'<b>参画ペース</b>＝参画クリエイター数÷掲載月数（承認の速さの目安）。'
        f'<b>1人あたりGMV</b>＝30日売上÷参画クリエイター数（1人あたりの取り分の目安）<br>')
    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} 週次おすすめ商品 {today}</title><style>{CSS}</style></head><body>
<div class="wrap">
<header><h1>📦 週次おすすめ商品</h1><span class="date">{today} 更新</span></header>
<div class="tabs">{tabs}</div>
{guide}
{_filter_bar(tbl)}
{_section(tbl, kind, embed_fn)}
<footer>⭐ <b>今週売れてる</b>＝直近7日間に投稿動画から売上が発生している商品（今から乗っても売れやすい）<br>
{badge_note}<b>成立率</b>＝その商品に参画したクリエイターのうち、実際に売上を出した人の割合。高いほど「乗れば売れる」商品です<br><br>
※ 報酬率・1件あたり報酬目安は取得時点の<b>参考値</b>です。実際の料率・条件は必ず各案件のアフィリエイトセンターで確認してください。<br>
⚠️ 薬機法注意タグの商品は投稿前に表現チェック相談へ。売上等の数値は独自集計の参考値です。</footer>
</div>{FILTER_JS}</body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


OWN_TOP_N = 5          # おすすめページでショップごとに表示する代表件数


def shop_slug(shop: str) -> str:
    """ショップ名 → 安定したファイル名 (週次再生成でもURLが変わらないようハッシュ)"""
    import hashlib
    return hashlib.md5(shop.encode("utf-8")).hexdigest()[:10]


def timesale_path(pid: str, prefix: str = "") -> str:
    return f"{prefix}timesale/{pid}.html"


def _own_card(r: dict, prefix: str = "", show_shop: bool = False,
              via_timesale: bool = False) -> str:
    """show_shop: ショップ見出しが無いページ (ライブタブ) だけショップ名を出す
    via_timesale: 遷移先をタイムセール設定依頼ページにする (ライブタブ)"""
    from weekly_picks import is_live, is_featured, live_label
    link = r.get("アフィリエイトリンク", "") or "#"
    if via_timesale and (r.get("商品ID") or "").strip():
        link = timesale_path(r["商品ID"].strip(), prefix)
    price = (r.get("価格", "") or "-").strip() or "-"
    rate = str(r.get("報酬率", "") or "").strip()
    rate = (rate + "%") if rate and not rate.endswith("%") else (rate or "-")
    shop = (r.get("ショップ") or "").strip()
    shop_html = ""
    if shop and show_shop:
        shop_html = (f'<div class="stats"><a class="shoplink" href="{prefix}shops/'
                     f'{shop_slug(shop)}.html">🏬 {_h.escape(shop)}</a></div>')
    pills = []
    if is_featured(r):
        pills.append('<span class="pill feat">⭐ イチオシ</span>')
    pills.append('<span class="pill own">🎁 自社サンプル可</span>')
    if is_live(r):
        pills.append(f'<span class="pill live">{live_label(r)}</span>')
    # 画像は自社ホスト (product-images/<商品ID>.jpeg)。無い商品は onerror で no image に落とす
    img_url = (r.get("画像") or "").strip()
    if img_url.startswith(("http", "/")):    # "/product-images/..." はリポジトリ同梱画像
        img = (f'<img src="{_h.escape(img_url)}" loading="lazy" alt="" '
               f"onerror=\"this.outerHTML='<div class=noimg>no image</div>'\">")
    else:
        img = '<div class="noimg">no image</div>'
    return (f'<div class="card">{img}<div class="body">'
            f'<div class="pills">{"".join(pills)}</div>'
            f'<a class="name" href="{_h.escape(link)}"{"" if via_timesale else " target=_blank"}>'
            f'{_h.escape(r.get("商品名", ""))}</a>'
            f'<div class="stats">価格 <b>{_h.escape(price)}</b>｜'
            f'報酬率※ <b class="reward">{_h.escape(rate)}</b></div>'
            f'{shop_html}</div></div>')


def _own_tabs(active: str, n_hot: int, n_chal: int, n_own: int, n_live: int,
              prefix: str = "") -> str:
    """おすすめ/ライブ/ショップ各ページ共通のタブ"""
    def cls(name, extra=""):
        return f'tab active {extra}' if active == name else 'tab'
    t = (f'<a class="{cls("hot","hot")}" href="{prefix or "./"}">🔥 売れ筋（{n_hot}）</a>'
         f'<a class="{cls("chal","chal")}" href="{prefix}challenge.html">🚀 新商品（{n_chal}）</a>'
         f'<a class="{cls("own","own")}" href="{prefix}recommend.html">🎁 おすすめ（{n_own}）</a>')
    if n_live:
        t += f'<a class="{cls("live","live")}" href="{prefix}live.html">📺 ライブ（{n_live}）</a>'
    t += f'<a class="tab arch" href="{prefix}archive/">📅 アーカイブ</a>'
    return t


def _own_doc(title: str, tabs: str, guide: str, chips: str, body: str, today: str,
             footer_extra: str = "") -> str:
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} {today}</title><style>{CSS}</style></head><body>
<div class="wrap">
<header><h1>📦 週次おすすめ商品</h1><span class="date">{today} 更新</span></header>
<div class="tabs">{tabs}</div>
{guide}
{chips}
{body}
<footer>{footer_extra}※ 報酬率は取得時点の<b>参考値</b>です。実際の料率・条件は必ず各案件のアフィリエイトセンターで確認してください。<br>
サンプル希望・質問は担当者まで。リンクは弊社のアフィリエイトリンクです。</footer>
</div>{FILTER_JS}</body></html>"""


def _group_by_shop(own_rows: list) -> "OrderedDict":
    """カテゴリ→ショップの順序を保ったままショップ単位にまとめる。
    ショップ内はシートの「表示」列がある商品を先頭に (それ以外はシート順を維持)"""
    from collections import OrderedDict
    from weekly_picks import is_featured
    shops = OrderedDict()
    for r in own_rows:
        key = (r.get("ショップ") or "その他").strip() or "その他"
        shops.setdefault(key, []).append(r)
    for k, items in shops.items():
        shops[k] = sorted(items, key=lambda r: 0 if is_featured(r) else 1)
    return shops


def _own_page(own_rows: list, out_path: str, today: str, n_hot: int, n_chal: int,
              n_live: int = 0, shop_prefix: str = ""):
    """🎁 おすすめ: ショップごとに代表 OWN_TOP_N 件 + ショップページへの導線。
    shop_prefix はショップページの参照先 (アーカイブからは本サイトの "/" を指す)"""
    shops = _group_by_shop(own_rows)
    cats, parts = [], []
    for shop, items in shops.items():
        cat = (items[0].get("カテゴリ") or "その他").strip() or "その他"
        if cat not in cats:
            cats.append(cat)
        parts.append(f'<div class="catgrp" data-cat="{_h.escape(cat)}">')
        parts.append(f'<div class="shop-h"><span class="shop-name">🏬 {_h.escape(shop)}</span>'
                     f'<span class="shop-n">{len(items)}件</span></div>')
        parts += [_own_card(r, prefix=shop_prefix) for r in items[:OWN_TOP_N]]
        if len(items) > OWN_TOP_N:
            parts.append(f'<a class="more" href="{shop_prefix}shops/{shop_slug(shop)}.html">'
                         f'このショップの全{len(items)}件を見る →</a>')
        parts.append('</div>')
    chips = ['<span class="chip on" data-cat="all">すべて</span>'] + [
        f'<span class="chip" data-cat="{_h.escape(c)}">{_h.escape(c)}</span>' for c in cats]
    guide = (f'<div class="guide"><div class="g-title">🎁 自社サンプル可の案件リスト</div>'
             f'弊社経由でサンプルを渡せる商品です。実績ゼロでもまずここから。'
             f'各ショップ代表{OWN_TOP_N}件を掲載しています（全{len(own_rows)}件・{len(shops)}ショップ）。'
             f'ショップ名をタップすると、そのショップの全商品を見られます。</div>')
    doc = _own_doc("🎁 おすすめ 週次おすすめ商品",
                   _own_tabs("own", n_hot, n_chal, len(own_rows), n_live),
                   guide, f'<div class="filters">{"".join(chips)}</div>',
                   "\n".join(parts), today)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


def _live_page(live_rows: list, out_path: str, today: str, n_hot: int, n_chal: int,
               n_own: int, shop_prefix: str = ""):
    """📺 ライブ: シートの「ライブ」列が立っている商品だけを集めたページ"""
    cats, parts = [], []
    from collections import OrderedDict
    by_cat = OrderedDict()
    for r in live_rows:
        by_cat.setdefault((r.get("カテゴリ") or "その他").strip() or "その他", []).append(r)
    for cat, items in by_cat.items():
        cats.append(cat)
        parts.append(f'<div class="catgrp" data-cat="{_h.escape(cat)}">')
        parts.append(f'<div class="cat">▼ <b>{_h.escape(cat)}</b>（{len(items)}件）</div>')
        parts += [_own_card(r, prefix=shop_prefix, show_shop=True, via_timesale=True)
                  for r in items]
        parts.append('</div>')
    chips = ['<span class="chip on" data-cat="all">すべて</span>'] + [
        f'<span class="chip" data-cat="{_h.escape(c)}">{_h.escape(c)}</span>' for c in cats]
    guide = ('<div class="guide"><div class="g-title">📺 LIVEタイムセール可能な商品</div>'
             'LIVE配信でタイムセールを設定できる商品です。商品をタップすると'
             '<b>タイムセール設定依頼ページ</b>が開きます。'
             'そこでショーケースに追加し、希望日程を送信してください。</div>')
    doc = _own_doc("📺 ライブ 週次おすすめ商品",
                   _own_tabs("live", n_hot, n_chal, n_own, len(live_rows)),
                   guide, f'<div class="filters">{"".join(chips)}</div>',
                   "\n".join(parts), today)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


TIMESALE_CSS = """
.panel{background:var(--card); border:1px solid var(--line); border-radius:14px;
       padding:16px; margin:14px 0}
.panel .name{font-weight:800; font-size:15px; margin:8px 0 6px; -webkit-line-clamp:none}
.demo-note{background:#fff3d6; color:#8a6100; border-radius:10px; padding:10px 12px;
           font-size:12.5px; margin-bottom:14px}
.step{display:flex; align-items:center; gap:8px; font-weight:800; font-size:15px; margin-bottom:10px}
.step .n{background:var(--ink); color:#fff; border-radius:99px; width:24px; height:24px;
         display:inline-flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0}
.btn{display:block; width:100%; text-align:center; padding:14px; border-radius:12px;
     font-weight:800; font-size:15px; border:none; cursor:pointer; text-decoration:none}
.btn.showcase{background:linear-gradient(90deg,#ff7a1a,#f97316); color:#fff}
.btn.submit{background:var(--ink); color:#fff; margin-top:14px}
.btn.submit:disabled{background:#c3c6cf; cursor:not-allowed}
.hint{color:var(--sub); font-size:12px; margin-top:8px}
label{display:block; font-weight:700; font-size:13px; margin:12px 0 6px}
input[type=text],textarea{width:100%; padding:11px 12px; border:1px solid var(--line);
     border-radius:10px; font-size:14px; background:#fff; font-family:inherit}
textarea{min-height:84px; resize:vertical; line-height:1.5}
.opt{color:var(--sub); font-weight:600; font-size:11.5px; margin-left:4px}
.cal-head{display:flex; justify-content:space-between; align-items:center; margin:12px 0 8px}
.cal-head .mon{font-weight:800; font-size:14px}
.cal-head button{border:1px solid var(--line); background:#fff; border-radius:8px;
     width:32px; height:32px; font-size:15px; cursor:pointer}
.cal{width:100%; border-collapse:collapse; table-layout:fixed}
.cal th{color:var(--sub); font-size:11px; font-weight:700; padding:4px 0}
.cal td{text-align:center; padding:2px 0}
.cal .d{display:inline-flex; align-items:center; justify-content:center;
        width:38px; height:38px; border-radius:10px; font-size:13.5px;
        font-variant-numeric:tabular-nums; cursor:pointer; user-select:none}
.cal .d.dis{color:#c3c6cf; cursor:not-allowed}
.cal .d.sel{background:#f97316; color:#fff; font-weight:800}
.cal .d.insel{background:#ffedd5; color:#9a3412; font-weight:700}
.picked{margin-top:12px; display:flex; flex-direction:column; gap:6px}
.picked .slot{display:flex; justify-content:space-between; align-items:center;
      background:#ffedd5; color:#9a3412; border-radius:10px; padding:8px 12px;
      font-weight:700; font-size:13px}
.picked .slot button{border:none; background:none; color:#9a3412; font-size:15px;
      cursor:pointer; font-weight:800}
.empty{color:var(--sub); font-size:12.5px; background:var(--tag-bg);
      border-radius:10px; padding:10px 12px; margin-top:12px}
.done{display:none; text-align:center; padding:30px 10px}
.done .big{font-size:40px}
.done h2{font-size:17px; margin:10px 0 6px}
"""

TIMESALE_JS = """
<script>
(function(){
  const MS = 86400000, BLOCK = 3, MAX_BLOCKS = 3, LEAD_DAYS = 2;
  const today = new Date(); today.setHours(0,0,0,0);
  const minStart = new Date(today.getTime() + LEAD_DAYS * MS);
  let view = new Date(today.getFullYear(), today.getMonth(), 1);
  let blocks = [];
  const $ = id => document.getElementById(id);
  const fmt = d => `${d.getMonth()+1}/${d.getDate()}`;
  const inBlock = (d, s) => d >= s && d < new Date(s.getTime() + BLOCK*MS);
  const findBlock = d => blocks.find(b => inBlock(d, b));
  const overlaps = s => blocks.some(b => Math.abs(s - b) < BLOCK*MS);
  function render(){
    $("mon").textContent = `${view.getFullYear()}年 ${view.getMonth()+1}月`;
    const first = new Date(view);
    let cur = new Date(first.getTime() - first.getDay()*MS);
    const body = $("cal-body"); body.innerHTML = "";
    for (let r = 0; r < 6; r++){
      const tr = document.createElement("tr");
      for (let c = 0; c < 7; c++){
        const td = document.createElement("td");
        if (cur.getMonth() === view.getMonth()){
          const d = new Date(cur), div = document.createElement("span");
          div.className = "d"; div.textContent = d.getDate();
          const blk = findBlock(d);
          if (blk) div.classList.add(+blk === +d ? "sel" : "insel");
          if (d < minStart) div.classList.add("dis");
          else div.addEventListener("click", () => {
            const hit = findBlock(d);
            if (hit) blocks = blocks.filter(b => +b !== +hit);
            else if (blocks.length >= MAX_BLOCKS){ alert("選択できるのは3枠までです。不要な枠を外してから選び直してください"); return; }
            else if (overlaps(d)){ alert("既に選択した3日間と重なっています"); return; }
            else { blocks.push(new Date(d)); blocks.sort((a,b)=>a-b); }
            render();
          });
          td.appendChild(div);
        }
        tr.appendChild(td);
        cur = new Date(cur.getTime() + MS);
      }
      body.appendChild(tr);
      if (cur.getMonth() !== view.getMonth() && cur > view) break;
    }
    const picked = $("picked"); picked.innerHTML = "";
    blocks.forEach(b => {
      const end = new Date(b.getTime() + (BLOCK-1)*MS);
      const slot = document.createElement("div"); slot.className = "slot";
      slot.innerHTML = `<span>🗓️ ${fmt(b)} 〜 ${fmt(end)}（3日間）</span>`;
      const x = document.createElement("button"); x.textContent = "✕";
      x.addEventListener("click", () => { blocks = blocks.filter(v => +v !== +b); render(); });
      slot.appendChild(x); picked.appendChild(slot);
    });
    $("empty").style.display = blocks.length ? "none" : "block";
    update();
  }
  function update(){ $("submit").disabled = !(blocks.length && $("acct").value.trim().length > 1); }
  $("acct").addEventListener("input", update);
  $("prev").addEventListener("click", () => { view = new Date(view.getFullYear(), view.getMonth()-1, 1); render(); });
  $("next").addEventListener("click", () => { view = new Date(view.getFullYear(), view.getMonth()+1, 1); render(); });
  $("submit").addEventListener("click", () => {
    const ranges = blocks.map(b => `${fmt(b)}〜${fmt(new Date(b.getTime()+(BLOCK-1)*MS))}`).join(" / ");
    const note = $("note").value.trim();
    $("done-detail").textContent = `${$("acct").value.trim()} さん｜希望日程: ${ranges}` + (note ? `｜備考: ${note}` : "");
    $("form-card").style.display = "none";
    $("done").style.display = "block";
    window.scrollTo({top: 0, behavior: "smooth"});
  });
  render();
})();
</script>"""


def _timesale_page(r: dict, out_path: str, today: str):
    """LIVE商品ごとのタイムセール設定依頼ページ (ショーケース追加 + 希望日程 + 備考)"""
    from weekly_picks import live_label
    name = _h.escape(r.get("商品名", ""))
    price = _h.escape((r.get("価格") or "-").strip() or "-")
    rate = str(r.get("報酬率", "") or "").strip()
    rate = _h.escape((rate + "%") if rate and not rate.endswith("%") else (rate or "-"))
    shop = _h.escape((r.get("ショップ") or "").strip())
    aff = _h.escape(r.get("アフィリエイトリンク", "") or "#")
    img_url = (r.get("画像") or "").strip()
    img = (f'<img src="{_h.escape(img_url)}" alt="" loading="lazy" '
           f"onerror=\"this.outerHTML='<div class=noimg>no image</div>'\">"
           if img_url.startswith(("http", "/")) else '<div class="noimg">no image</div>')
    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>タイムセール設定依頼｜{name}</title>
<style>{CSS}{TIMESALE_CSS}</style></head><body>
<div class="wrap">
<a class="more back" href="../live.html">← 📺 ライブ一覧に戻る</a>
<header style="margin-top:10px"><h1>🔥 タイムセール設定依頼</h1></header>
<div class="card">{img}<div class="body">
<div class="pills"><span class="pill own">🎁 自社サンプル可</span>
<span class="pill live">{live_label(r)}</span></div>
<div class="name">{name}</div>
<div class="stats">価格 <b>{price}</b>｜報酬率※ <b class="reward">{rate}</b></div>
<div class="stats">🏬 {shop}</div>
</div></div>

<div class="panel">
  <div class="step"><span class="n">1</span>まずはショーケースに追加</div>
  <a class="btn showcase" href="{aff}" target="_blank">🛒 ショーケースに追加する</a>
  <div class="hint">タップするとTikTokの商品ページが開きます</div>
</div>

<div class="panel" id="form-card">
  <div class="step"><span class="n">2</span>タイムセールの希望日程を選択</div>
  <div class="hint" style="margin-top:0">タイムセールは<b>3日間単位</b>です。開始日をタップすると3日分が選択されます（<b>最大3枠</b>・本日から2日間は選択不可）</div>
  <div class="cal-head">
    <button id="prev" aria-label="前の月">‹</button>
    <span class="mon" id="mon"></span>
    <button id="next" aria-label="次の月">›</button>
  </div>
  <table class="cal"><thead><tr>
    <th>日</th><th>月</th><th>火</th><th>水</th><th>木</th><th>金</th><th>土</th>
  </tr></thead><tbody id="cal-body"></tbody></table>
  <div id="picked" class="picked"></div>
  <div id="empty" class="empty">まだ日程が選択されていません。カレンダーから開始日をタップしてください</div>
  <label for="acct">TikTokアカウント名（@から）</label>
  <input type="text" id="acct" placeholder="@your_account">
  <label for="note">備考<span class="opt">任意</span></label>
  <textarea id="note" placeholder="希望時間帯、LIVE予定、サンプルの相談など自由にご記入ください"></textarea>
  <button class="btn submit" id="submit" disabled>この内容で依頼する</button>
</div>

<div class="panel done" id="done">
  <div class="big">✅</div>
  <h2>依頼を受け付けました</h2>
  <p class="stats" id="done-detail"></p>
  <p class="stats" style="margin-top:8px">担当者が内容を確認してタイムセールを設定します。</p>
</div>

<footer>※ 報酬率は取得時点の<b>参考値</b>です。タイムセールの設定可否・時間帯は在庫や施策状況により調整される場合があります。</footer>
</div>{TIMESALE_JS}</body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


def _timesale_pages(live_rows: list, out_dir: str, today: str) -> int:
    import os
    d = os.path.join(out_dir, "timesale")
    os.makedirs(d, exist_ok=True)
    n = 0
    for r in live_rows:
        pid = (r.get("商品ID") or "").strip()
        if not pid:
            continue
        _timesale_page(r, os.path.join(d, f"{pid}.html"), today)
        n += 1
    return n


def _shop_pages(own_rows: list, out_dir: str, today: str, n_hot: int, n_chal: int,
                n_live: int):
    """shops/<hash>.html にショップごとの全商品ページを生成"""
    import os
    shops = _group_by_shop(own_rows)
    shop_dir = os.path.join(out_dir, "shops")
    os.makedirs(shop_dir, exist_ok=True)
    for shop, items in shops.items():
        cat = (items[0].get("カテゴリ") or "その他").strip() or "その他"
        guide = (f'<div class="guide"><div class="g-title">🏬 {_h.escape(shop)}</div>'
                 f'{_h.escape(cat)}｜全{len(items)}件。すべて弊社経由でサンプル相談ができます。</div>'
                 f'<a class="more back" href="../recommend.html">← 🎁 おすすめ一覧に戻る</a>')
        body = "\n".join(_own_card(r, prefix="../") for r in items)
        doc = _own_doc(f"🏬 {_h.escape(shop)}",
                       _own_tabs("", n_hot, n_chal, len(own_rows), n_live, prefix="../"),
                       guide, "", body, today)
        with open(os.path.join(shop_dir, f"{shop_slug(shop)}.html"), "w",
                  encoding="utf-8") as f:
            f.write(doc)
    return len(shops)


def write_site(hot, new_tbl, out_dir: str, embed: bool = False, own_rows: list | None = None):
    import os
    from weekly_picks import is_live
    os.makedirs(out_dir, exist_ok=True)
    embed_fn = make_embed_fn() if embed else None
    today = dt.date.today().strftime("%Y/%m/%d")
    own_rows = own_rows or []
    live_rows = [r for r in own_rows if is_live(r)]
    n_own, n_live = len(own_rows), len(live_rows)
    _page(hot, "hot", os.path.join(out_dir, "index.html"),
          embed_fn, today, len(hot), len(new_tbl), n_own, n_live)
    _page(new_tbl, "challenge", os.path.join(out_dir, "challenge.html"),
          embed_fn, today, len(hot), len(new_tbl), n_own, n_live)
    if own_rows:
        _own_page(own_rows, os.path.join(out_dir, "recommend.html"),
                  today, len(hot), len(new_tbl), n_live)
        _shop_pages(own_rows, out_dir, today, len(hot), len(new_tbl), n_live)
        if live_rows:
            _live_page(live_rows, os.path.join(out_dir, "live.html"),
                       today, len(hot), len(new_tbl), n_own)
            _timesale_pages(live_rows, out_dir, today)


# ============================================================
# アーカイブ (過去週スナップショット + data JSON + 一覧ページ)
# ============================================================
def _to_archive(doc: str, date_str: str) -> str:
    """生成済みページをアーカイブ用に変換: 注意バナー挿入 + アーカイブリンクを一覧へ"""
    note = (f'<div class="arch-note">📌 これは <b>{date_str}</b> 時点のアーカイブです。'
            f'<a href="../">アーカイブ一覧</a>｜<a href="/">最新のランキングを見る</a></div>')
    doc = doc.replace('</header>', '</header>' + note, 1)
    return doc.replace('href="./archive/"', 'href="../"')


def archive_site(hot, new_tbl, root_dir: str = ".", date_str: str | None = None,
                 own_rows: list | None = None):
    """archive/<日付>/ にスナップショット保存 + data/<日付>.json + 一覧ページ更新"""
    import json
    import os
    date_str = date_str or dt.date.today().strftime("%Y-%m-%d")
    arch_dir = os.path.join(root_dir, "archive", date_str)
    os.makedirs(arch_dir, exist_ok=True)
    today = dt.date.today().strftime("%Y/%m/%d")
    from weekly_picks import is_live
    own_rows = own_rows or []
    live_rows = [r for r in own_rows if is_live(r)]
    n_own, n_live = len(own_rows), len(live_rows)
    _page(hot, "hot", os.path.join(arch_dir, "index.html"),
          None, today, len(hot), len(new_tbl), n_own, n_live)
    _page(new_tbl, "challenge", os.path.join(arch_dir, "challenge.html"),
          None, today, len(hot), len(new_tbl), n_own, n_live)
    pages = ["index.html", "challenge.html"]
    if own_rows:
        # ショップページ本体はアーカイブに複製せず本サイト側 (/shops/) を参照する
        _own_page(own_rows, os.path.join(arch_dir, "recommend.html"),
                  today, len(hot), len(new_tbl), n_live, shop_prefix="/")
        pages.append("recommend.html")
        if live_rows:
            _live_page(live_rows, os.path.join(arch_dir, "live.html"),
                       today, len(hot), len(new_tbl), n_own, shop_prefix="/")
            pages.append("live.html")
    for fn in pages:
        p = os.path.join(arch_dir, fn)
        with open(p, encoding="utf-8") as f:
            doc = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write(_to_archive(doc, date_str))
    # 表示テーブルをJSONでも蓄積 (先週比・連続ランクイン等の将来機能の材料)
    data_dir = os.path.join(root_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    payload = {"date": date_str, "n_hot": len(hot), "n_challenge": len(new_tbl),
               "hot": hot.to_dict(orient="records"),
               "challenge": new_tbl.to_dict(orient="records")}
    with open(os.path.join(data_dir, f"{date_str}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, default=str)
    write_archive_index(root_dir)
    return arch_dir


def write_archive_index(root_dir: str = "."):
    """archive/ 配下の日付フォルダを走査して一覧ページを再生成"""
    import json
    import os
    import re
    arch_root = os.path.join(root_dir, "archive")
    os.makedirs(arch_root, exist_ok=True)
    dates = sorted(
        (d for d in os.listdir(arch_root)
         if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)
         and os.path.exists(os.path.join(arch_root, d, "index.html"))),
        reverse=True)
    rows = []
    for d in dates:
        counts = ""
        jpath = os.path.join(root_dir, "data", f"{d}.json")
        if os.path.exists(jpath):
            try:
                with open(jpath, encoding="utf-8") as f:
                    j = json.load(f)
                counts = (f'<span class="stats">🔥 売れ筋 {j["n_hot"]}件 / '
                          f'🚀 新商品 {j["n_challenge"]}件</span>')
            except Exception:
                pass
        rows.append(f'<a class="card week" href="./{d}/">'
                    f'<span class="wk">📦 {d}</span>{counts}</a>')
    body = "\n".join(rows) or '<p class="stats">まだアーカイブがありません</p>'
    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>📅 過去のランキング｜週次おすすめ商品</title><style>{CSS}
.card.week{{align-items:center; justify-content:space-between; text-decoration:none}}
.card.week .wk{{font-weight:800; font-size:15px; color:var(--ink)}}
.card.week:hover{{border-color:var(--ink)}}</style></head><body>
<div class="wrap">
<header><h1>📅 過去のランキング</h1></header>
<div class="tabs"><a class="tab" href="/">🔥 最新の売れ筋</a>
<a class="tab" href="/challenge.html">🚀 最新の新商品</a></div>
{body}
<footer>毎週の更新時に自動保存されるアーカイブです。数値・報酬率は各時点の参考値で、現在の条件とは異なる場合があります。</footer>
</div></body></html>"""
    with open(os.path.join(arch_root, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
