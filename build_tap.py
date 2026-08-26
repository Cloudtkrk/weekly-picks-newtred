# -*- coding: utf-8 -*-
"""tap.html を生成し、既存ページのタブに 🤝案件 を差し込む。
   使い方: python build_tap.py
"""
import re, sys, datetime, glob, os
import report_html as R
import tap_site

def counts(path="index.html"):
    s = open(path, encoding="utf-8").read()
    def g(p, d=0):
        m = re.search(p, s)
        return int(m.group(1)) if m else d
    return (g(r"🔥 売れ筋（(\d+)）"), g(r"🚀 新商品（(\d+)）"),
            g(r"🎁 おすすめ（(\d+)）"), g(r"📺 ライブ（(\d+)）"))

def main():
    n_hot, n_chal, n_own, n_live = counts()
    prods, camps = tap_site.load_tap(".")
    if not prods:
        print("tap_list.csv が無いのでスキップ"); return
    R.TAP_TAB_N = len(prods)
    today = datetime.date.today().isoformat()
    n = tap_site.write_tap_page("tap.html", ".", today, n_hot, n_chal, n_own, n_live)
    print(f"tap.html 生成: {n}商品 / {len(camps)}案件")

    # 既存ページのタブ行に 🤝案件 を差し込む (再生成せずHTMLを直接パッチ)
    tab = (f'<a class="tab" href="./tap.html">🤝 案件（{n}）</a>')
    tab_sub = (f'<a class="tab" href="../tap.html">🤝 案件（{n}）</a>')
    pat = re.compile(r'(<a class="tab[^"]*" href="(?:\./|\.\./)?challenge\.html">🚀 新商品（\d+）</a>)')
    targets = ["index.html", "challenge.html", "recommend.html", "live.html"] \
              + sorted(glob.glob("shops/*.html"))
    patched = 0
    for f in targets:
        if not os.path.exists(f): continue
        s = open(f, encoding="utf-8").read()
        if "tap.html" in s: continue
        t = tab_sub if "/" in f else tab
        s2, k = pat.subn(lambda m: m.group(1) + t, s, count=1)
        if k:
            open(f, "w", encoding="utf-8").write(s2); patched += 1
    print(f"タブ差し込み: {patched}ページ")

if __name__ == "__main__":
    main()
