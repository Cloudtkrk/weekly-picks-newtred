import json, csv, re, os, shutil, collections, unicodedata, datetime

rows=json.load(open('tap_rows_raw.json'))
rows += [
 dict(cid='7671148890171574024', name='Seika全シャンプー  コンディショナー アミノ酸シャンプー  頭皮ケア 頭皮 髪 すっきり洗浄 和漢  日本製 セイカゼン ZEN', pid='1736735168837683127', price='777円-8,360円', shop='OUJISHOP 王子製薬', start='07/08/2026 00:00:00', end='01/08/2027 23:59:59', rate='9.00%', aff='https://affiliate.tiktok.com/api/v1/share/ALKc32280LDH', url='', src='sheet:王子製薬'),
 dict(cid='7671148890171574024', name='【期間限定おまけ付き!!】Seika全シャンプー  コンディショナー アミノ酸シャンプー  頭皮ケア 頭皮 髪 すっきり洗浄 和漢  日本製 セイカゼン ZEN', pid='1732202493604104119', price='3,837円-6,336円', shop='OUJISHOP 王子製薬', start='07/08/2026 00:00:00', end='01/08/2027 23:59:59', rate='9.00%', aff='https://affiliate.tiktok.com/api/v1/share/ALKc4PQLWLMR', url='', src='sheet:王子製薬'),
]

camps={c['cid']:c for c in json.load(open('campaigns.json'))}

# ---- own_list for category enrichment ----
own={}
ownname={}
def norm(s):
    s=unicodedata.normalize('NFKC', str(s)).lower()
    return re.sub(r'[^0-9a-z぀-ヿ一-鿿]','',s)[:30]
with open('/home/claude/wp/own_list.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        own[str(r['商品ID']).strip()]=r
        ownname.setdefault(norm(r['商品名']), r)

def isod(s):
    """TikTokエクスポートの 'dd/mm/YYYY HH:MM:SS' を ISO日付に"""
    try:
        return datetime.datetime.strptime(str(s).split()[0], '%d/%m/%Y').date().isoformat()
    except Exception:
        return ''

def pct(s):
    m=re.search(r'([\d.]+)', str(s))
    return float(m.group(1)) if m else 0.0

from cats import Classifier
CLF=None

import csv as _csv
CLF=Classifier(list(_csv.DictReader(open('/home/claude/wp/own_list.csv', encoding='utf-8'))))
IMG_SRC='/home/claude/tap/images'
have=set(os.path.splitext(f)[0] for f in os.listdir('/home/claude/wp/product-images'))
newimg=0
out=[]
for r in rows:
    pid=r['pid']
    c=camps.get(r['cid'], {})
    o=own.get(pid) or ownname.get(norm(r['name']))
    cat, how = CLF.classify(pid, r['name'], r['shop'])
    src=os.path.join(IMG_SRC, pid+'.jpeg')
    if os.path.exists(src) and pid not in have:
        shutil.copy(src, '/home/claude/wp/product-images/'+pid+'.jpeg'); have.add(pid); newimg+=1
    img = ('product-images/%s.jpeg'%pid) if pid in have else ((o or {}).get('画像') or '')
    out.append(dict(
        campaign=c.get('name',''), campaign_id=r['cid'], shop=r['shop'], category=cat, cat_src=how,
        name=r['name'], price=r['price'], rate=pct(r['rate']), aff=r['aff'], product_id=pid,
        image=img, start=isod(r['start']), end=isod(r['end']),
        live='⚪︎' if (o or {}).get('ライブ') else '',
    ))
# dedupe: same pid in multiple campaigns -> keep highest rate
best={}
for x in out:
    k=x['product_id']
    if k not in best or x['rate']>best[k]['rate']: best[k]=x
uniq=sorted(best.values(), key=lambda x:(-x['rate'], x['shop']))

with open('/home/claude/wp/tap_list.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(uniq[0].keys())); w.writeheader(); w.writerows(uniq)

# campaign csv
crows=[]
agg=collections.defaultdict(lambda: dict(n=0, cats=collections.Counter(), rates=[], starts=[],
                                         shops=collections.Counter(), reps=[]))
for x in out:
    a=agg[x['campaign_id']]; a['n']+=1; a['cats'][x['category']]+=1; a['rates'].append(x['rate'])
    if x['start']: a['starts'].append(x['start'])
    a['shops'][x['shop']]+=1
    if x['image']: a['reps'].append(x)
for cid,c in camps.items():
    a=agg.get(cid, dict(n=0,cats=collections.Counter(),rates=[],starts=[],
                        shops=collections.Counter(),reps=[]))
    # 代表商品 = 画像があるもののうち料率が最も高い商品
    rep=max(a['reps'], key=lambda x:(x['rate'], x['start'])) if a['reps'] else None
    shops=a['shops']
    crows.append(dict(campaign=c['name'], campaign_id=cid, shop=c['shop'], products=c['n'],
        rate_min=min(a['rates']) if a['rates'] else 0, rate_max=max(a['rates']) if a['rates'] else 0,
        rate_label=c['rate'], rate_detail=c['detail'],
        categories='／'.join(k for k,_ in a['cats'].most_common(3)),
        started=min(a['starts']) if a['starts'] else '',
        latest=max(a['starts']) if a['starts'] else '',
        shop_count=len(shops),
        rep_image=rep['image'] if rep else '',
        rep_name=rep['name'] if rep else ''))
crows.sort(key=lambda x:(x['latest'] or '', x['products']), reverse=True)
with open('/home/claude/wp/tap_campaigns.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(crows[0].keys())); w.writeheader(); w.writerows(crows)

print('tap rows', len(out), 'unique products', len(uniq), 'new images copied', newimg)
print('campaigns', len(crows))
print('categories', collections.Counter(x['category'] for x in uniq).most_common())
print('matched to own_list', sum(1 for x in out if own.get(x['product_id'])))
