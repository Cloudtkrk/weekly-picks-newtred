# -*- coding: utf-8 -*-
"""🤝 TAP案件検索ページ (tap.html) の生成。

TAP一覧スプレッドシート由来の `tap_list.csv` / `tap_campaigns.csv` を読み、
スマホ前提の統合検索UI (商品で探す / 案件で探す の2ビュー) を静的HTMLで出力する。
データはページ内にJSONで埋め込むのでサーバー不要。
"""
from __future__ import annotations
import csv, json, os, html as _h, datetime as _dt

from report_html import CSS, _write, _own_tabs
from weekly_picks import CONFIG

TAP_CSS = """
.tapg{padding:10px 13px; margin:12px 0 0}
.tapg summary{cursor:pointer; list-style:none; font-size:12.5px; color:var(--sub);
     display:flex; align-items:center; gap:8px; flex-wrap:wrap}
.tapg summary::-webkit-details-marker{display:none}
.tapg summary b{color:var(--ink)}
.gmore{margin-left:auto; color:#0ea5e9; font-weight:800; white-space:nowrap}
.tapg[open] .gmore{visibility:hidden}
.gbody{margin-top:9px; padding-top:9px; border-top:1px solid var(--line);
     font-size:12.5px; color:var(--sub); line-height:1.7}
.seg{display:flex; gap:6px; background:var(--card); border:1px solid var(--line);
     border-radius:12px; padding:4px; margin:14px 0 4px}
.seg button{flex:1; border:0; background:transparent; font:inherit; font-weight:800;
     font-size:13.5px; color:var(--sub); padding:9px 6px; border-radius:9px; cursor:pointer}
.seg button.on{background:var(--ink); color:#fff}
.searchbar{position:sticky; top:0; z-index:20; background:var(--bg);
     padding:10px 0 6px; margin:0 -16px; padding-left:16px; padding-right:16px}
.searchbar input{width:100%; padding:12px 14px; border:1px solid var(--line);
     border-radius:12px; font:inherit; font-size:16px; background:var(--card); color:var(--ink)}
.searchbar input:focus{outline:2px solid var(--ink); outline-offset:-2px}
.frow{display:flex; gap:6px; overflow-x:auto; scrollbar-width:none;
      margin:8px -16px 0; padding:0 16px 2px}
.frow::-webkit-scrollbar{display:none}
.frow .chip{white-space:nowrap; flex-shrink:0}
.sortrow{display:flex; align-items:center; justify-content:space-between; gap:10px;
     margin:10px 0 2px; font-size:12.5px; color:var(--sub)}
.sortrow select{font:inherit; font-size:12.5px; padding:6px 26px 6px 10px; border-radius:9px;
     border:1px solid var(--line); background:var(--card); color:var(--ink); appearance:none;
     background-image:linear-gradient(45deg,transparent 50%,var(--sub) 50%),linear-gradient(135deg,var(--sub) 50%,transparent 50%);
     background-position:calc(100% - 14px) 52%,calc(100% - 9px) 52%;
     background-size:5px 5px,5px 5px; background-repeat:no-repeat}
.hits b{color:var(--ink)}
.grid{display:grid; grid-template-columns:1fr; gap:8px; margin-top:8px}
.pcard{display:flex; gap:12px; background:var(--card); border:1px solid var(--line);
     border-radius:12px; padding:11px; text-decoration:none; color:inherit}
.pcard:active{background:#fafbfd}
.pcard img{width:74px; height:74px; object-fit:cover; border-radius:9px;
     background:var(--tag-bg); flex-shrink:0}
.pcard .noimg{width:74px; height:74px; border-radius:9px; background:var(--tag-bg);
     display:flex; align-items:center; justify-content:center; color:var(--sub);
     font-size:10px; flex-shrink:0}
.pb{min-width:0; flex:1}
.pname{font-weight:700; font-size:13.5px; line-height:1.45; margin:2px 0 5px;
     overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical}
.pmeta{color:var(--sub); font-size:12px; display:flex; gap:8px; flex-wrap:wrap;
     align-items:baseline}
.prate{color:var(--hot); font-weight:800; font-size:14px; font-variant-numeric:tabular-nums}
.pprice{font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums}
.pshop{display:block; color:var(--sub); font-size:11.5px; overflow:hidden;
     text-overflow:ellipsis; white-space:nowrap}
.ccard{display:block; background:var(--card); border:1px solid var(--line);
     border-radius:12px; padding:13px 14px; text-decoration:none; color:inherit; cursor:pointer}
.ccard:active{background:#fafbfd}
.ch{display:flex; align-items:baseline; justify-content:space-between; gap:10px}
.cname{font-weight:800; font-size:14.5px; line-height:1.4}
.crate{color:var(--hot); font-weight:800; font-size:15px; white-space:nowrap;
     font-variant-numeric:tabular-nums}
.cmeta{color:var(--sub); font-size:12px; margin-top:6px}
.cbar{display:flex; gap:4px; margin-top:9px; flex-wrap:wrap}
.empty{text-align:center; color:var(--sub); padding:44px 10px; font-size:13px}
.more2{display:block; width:100%; text-align:center; padding:12px; margin:12px 0 0;
     background:var(--card); border:1px solid var(--line); border-radius:11px;
     font:inherit; font-size:13px; font-weight:800; color:var(--ink); cursor:pointer}
.active-filter{display:flex; align-items:center; gap:8px; background:#fff3d6; color:#8a6100;
     border-radius:10px; padding:9px 12px; margin:10px 0 0; font-size:12.5px; font-weight:700}
.active-filter button{margin-left:auto; border:0; background:#8a6100; color:#fff;
     border-radius:99px; font:inherit; font-size:11px; font-weight:800; padding:3px 10px; cursor:pointer}
@media(min-width:700px){.grid{grid-template-columns:1fr 1fr}}
@media(max-width:380px){.pcard img,.pcard .noimg{width:62px;height:62px}}
"""


def _num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def load_tap(root="."):
    """tap_list.csv / tap_campaigns.csv を読む。無ければ (None, None)。"""
    p, c = os.path.join(root, "tap_list.csv"), os.path.join(root, "tap_campaigns.csv")
    if not (os.path.exists(p) and os.path.exists(c)):
        return None, None
    with open(p, encoding="utf-8") as f:
        prods = list(csv.DictReader(f))
    with open(c, encoding="utf-8") as f:
        camps = list(csv.DictReader(f))
    return prods, camps


def _payload(prods, camps):
    P = [{
        "n": r["name"], "s": r["shop"], "c": r["category"], "k": r["campaign"],
        "r": _num(r["rate"]), "p": r["price"], "u": r["aff"], "i": r["image"],
        "l": 1 if r.get("live") else 0,
    } for r in prods]
    C = [{
        "k": r["campaign"], "s": r["shop"], "n": int(r["products"] or 0),
        "lo": _num(r["rate_min"]), "hi": _num(r["rate_max"]),
        "rl": r["rate_label"], "cat": r["categories"],
    } for r in camps]
    return P, C


def write_tap_page(out_path="tap.html", root=".", today=None,
                   n_hot=0, n_chal=0, n_own=0, n_live=0):
    prods, camps = load_tap(root)
    if not prods:
        return 0
    today = today or _dt.date.today().isoformat()
    P, C = _payload(prods, camps)
    cats = sorted({r["category"] for r in prods})
    max_rate = max(p["r"] for p in P)

    tabs = _own_tabs("tap", n_hot, n_chal, n_own, n_live)
    chips = "".join(f'<span class="chip" data-cat="{_h.escape(c)}">{_h.escape(c)}</span>'
                    for c in cats)

    guide = f"""<details class="guide tapg"><summary>🤝 <b>{len(camps)}案件・{len(P)}商品</b>　弊社の提携案件だけを集めたページです<span class="gmore">詳しく</span></summary>
<div class="gbody">弊社がセラーと直接結んでいる<b>パートナーコラボ案件</b>です。ここに出ている料率は
<b>弊社所属クリエイター向けの確定料率</b>（通常のオープンコラボより高く設定しています）。
商品をタップするとそのままショーケースに追加できます。<br>
案件によっては料率が商品ごとに分かれています（例: 12%〜17%）。
「案件で探す」から案件を選ぶと、その案件の商品だけに絞り込めます。（{today} 時点）</div></details>"""

    body = f"""
{guide}
<div class="seg" id="seg">
  <button data-v="p" class="on">🛍 商品で探す（{len(P)}）</button>
  <button data-v="c">🏷 案件で探す（{len(C)}）</button>
</div>
<div class="searchbar"><input id="q" type="search" placeholder="商品名・ショップ名・案件名で検索"
   autocomplete="off" enterkeyhint="search"></div>
<div class="frow" id="cats"><span class="chip on" data-cat="">すべて</span>{chips}</div>
<div class="frow" id="rates">
  <span class="chip on" data-min="0">料率すべて</span>
  <span class="chip" data-min="10">10%以上</span>
  <span class="chip" data-min="15">15%以上</span>
  <span class="chip" data-min="20">20%以上</span>
  <span class="chip" data-min="25">25%以上</span>
</div>
<div id="af"></div>
<div class="sortrow">
  <span class="hits" id="hits"></span>
  <select id="sort">
    <option value="rate">料率が高い順</option>
    <option value="price">価格が安い順</option>
    <option value="name">名前順</option>
  </select>
</div>
<div class="grid" id="list"></div>
<button class="more2" id="more" hidden>もっと見る</button>
<div class="empty" id="empty" hidden>該当する商品がありません。<br>検索条件を変えてみてください。</div>
"""

    footer = ("🤝 <b>TAP案件</b>＝弊社とセラーの提携案件。表示している料率は弊社所属クリエイター向けの"
              "設定値です（申請状況・期間により変動する場合があります）。<br>")

    data = json.dumps({"P": P, "C": C, "maxRate": max_rate},
                      ensure_ascii=False, separators=(",", ":"))

    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🤝 TAP案件を探す｜週次おすすめ商品 {today}</title>
<style>{CSS}{TAP_CSS}</style></head><body>
<div class="wrap">
<header><h1>📦 週次おすすめ商品</h1><span class="date">{today} 更新</span></header>
<div class="tabs">{tabs}</div>
{body}
<footer>{footer}※ 料率・条件は取得時点の<b>参考値</b>です。実際の条件は必ずアフィリエイトセンターでご確認ください。<br>
サンプル希望・質問は担当者まで。リンクは弊社のアフィリエイトリンクです。</footer>
</div>
<script>const DATA={data};{TAP_JS}</script>
</body></html>"""
    _write(out_path, doc)
    return len(P)


TAP_JS = r"""
(function(){
  var P=DATA.P, C=DATA.C, PAGE=40;
  var st={v:'p', q:'', cat:'', min:0, sort:'rate', camp:'', shown:PAGE};
  var $=function(id){return document.getElementById(id)};
  var esc=function(s){return String(s).replace(/[&<>"']/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
  var norm=function(s){return String(s).toLowerCase()};
  P.forEach(function(p){p._t=norm(p.n+' '+p.s+' '+p.k)});
  C.forEach(function(c){c._t=norm(c.k+' '+c.s+' '+c.cat)});
  var priceNum=function(s){var m=String(s).replace(/,/g,'').match(/(\d+)/);return m?+m[1]:1e12};

  function filtered(){
    var q=st.q, out=[];
    if(st.v==='c'){
      for(var i=0;i<C.length;i++){var c=C[i];
        if(q&&c._t.indexOf(q)<0) continue;
        if(st.min&&c.hi<st.min) continue;
        if(st.cat&&String(c.cat).indexOf(st.cat)<0) continue;
        out.push(c);}
      out.sort(st.sort==='name'?function(a,b){return a.k.localeCompare(b.k,'ja')}
        :function(a,b){return b.hi-a.hi||b.n-a.n});
      return out;
    }
    for(var j=0;j<P.length;j++){var p=P[j];
      if(st.camp&&p.k!==st.camp) continue;
      if(q&&p._t.indexOf(q)<0) continue;
      if(st.cat&&p.c!==st.cat) continue;
      if(st.min&&p.r<st.min) continue;
      out.push(p);}
    if(st.sort==='price') out.sort(function(a,b){return priceNum(a.p)-priceNum(b.p)});
    else if(st.sort==='name') out.sort(function(a,b){return a.n.localeCompare(b.n,'ja')});
    else out.sort(function(a,b){return b.r-a.r});
    return out;
  }

  function pcard(p){
    var img=p.i?'<img src="'+esc(p.i)+'" alt="" loading="lazy" decoding="async" '+
      'onerror="this.outerHTML=\'<div class=noimg>no image</div>\'">':'<div class="noimg">no image</div>';
    return '<a class="pcard" href="'+esc(p.u)+'" target="_blank" rel="noopener">'+img+
      '<div class="pb"><span class="pshop">'+esc(p.s)+'</span>'+
      '<div class="pname">'+esc(p.n)+'</div>'+
      '<div class="pmeta"><span class="prate">'+p.r+'%</span>'+
      '<span class="pprice">'+esc(p.p)+'</span>'+
      (p.l?'<span class="tag">📺 LIVE可</span>':'')+'</div></div></a>';
  }
  function ccard(c){
    var rate=c.lo===c.hi?c.lo+'%':c.lo+'%〜'+c.hi+'%';
    return '<div class="ccard" data-camp="'+esc(c.k)+'">'+
      '<div class="ch"><div class="cname">'+esc(c.k)+'</div><div class="crate">'+rate+'</div></div>'+
      '<div class="cmeta">'+esc(c.s)+'</div>'+
      '<div class="cbar"><span class="tag">商品 '+c.n+'件</span>'+
      (c.cat?'<span class="tag">'+esc(c.cat).split('／').join('</span><span class="tag">')+'</span>':'')+
      '</div></div>';
  }

  function render(){
    var rows=filtered(), n=rows.length;
    $('hits').innerHTML=st.v==='c'?('<b>'+n+'</b> 案件'):('<b>'+n+'</b> 商品');
    $('empty').hidden=n>0;
    var slice=rows.slice(0, st.shown);
    $('list').innerHTML=slice.map(st.v==='c'?ccard:pcard).join('');
    $('more').hidden=n<=st.shown;
    $('more').textContent='もっと見る（残り'+(n-st.shown)+'件）';
    $('af').innerHTML=st.camp?('<div class="active-filter">🏷 '+esc(st.camp)+
      ' の商品を表示中<button id="clr">解除</button></div>'):'';
    var s=$('sort');
    s.options[1].hidden = st.v==='c';
    var sel=document.querySelectorAll('#sort option');
    if(st.v==='c'&&st.sort==='price'){st.sort='rate'; s.value='rate'}
  }
  function reset(){st.shown=PAGE; render()}

  $('q').addEventListener('input',function(e){st.q=norm(e.target.value.trim()); reset()});
  $('sort').addEventListener('change',function(e){st.sort=e.target.value; reset()});
  $('more').addEventListener('click',function(){st.shown+=PAGE*2; render()});
  document.getElementById('seg').addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b) return;
    st.v=b.dataset.v; st.camp='';
    [].forEach.call(this.children,function(x){x.classList.toggle('on',x===b)});
    reset(); window.scrollTo({top:0,behavior:'smooth'});
  });
  function chipRow(id, key, attr){
    document.getElementById(id).addEventListener('click',function(e){
      var c=e.target.closest('.chip'); if(!c) return;
      [].forEach.call(this.children,function(x){x.classList.toggle('on',x===c)});
      st[key]= attr==='min'? (+c.dataset.min||0) : (c.dataset.cat||'');
      reset();
    });
  }
  chipRow('cats','cat','cat'); chipRow('rates','min','min');
  document.getElementById('list').addEventListener('click',function(e){
    var c=e.target.closest('.ccard'); if(!c) return;
    st.camp=c.dataset.camp; st.v='p'; st.q=''; $('q').value='';
    var seg=document.getElementById('seg').children;
    seg[0].classList.add('on'); seg[1].classList.remove('on');
    reset(); window.scrollTo({top:0,behavior:'smooth'});
  });
  document.getElementById('af').addEventListener('click',function(e){
    if(e.target.id==='clr'){st.camp=''; reset()}
  });
  render();
})();
"""
