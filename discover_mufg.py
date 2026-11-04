#!/usr/bin/env python3
"""Discover MUFG fund codes using the asset manager's published code-list API.
Discovery only: no unverified codes or NAV values are written to nav.json.
"""
import json, pathlib, urllib.request, unicodedata
ROOT=pathlib.Path(__file__).resolve().parent
FUNDS=json.loads((ROOT/'funds.json').read_text(encoding='utf-8'))
TARGETS={'f25':'純金ファンド','f38':'マイストライカー','f39':'マイフォワード','f40':'マイミッドフィルダー','f41':'マイディフェンダー'}
def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKC',str(s)).lower() if c.isalnum())
def objects(node):
    if isinstance(node,dict):
        if any(k in node for k in ('fund_name','fund_cd','association_fund_cd')):
            yield node
        for v in node.values(): yield from objects(v)
    elif isinstance(node,list):
        for v in node: yield from objects(v)
report={'source':'https://developer.am.mufg.jp/code_list','status':'not_checked','candidates':{},'error':None}
try:
    req=urllib.request.Request(report['source'],headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=30) as resp: raw=resp.read(5000000)
    data=json.loads(raw)
    entries=list(objects(data))
    report['status']='retrieved'\n    report['response_type']=type(data).__name__\n    report['top_level_keys']=list(data.keys())[:20] if isinstance(data,dict) else []\n    report['first_record']=entries[0] if entries else None
    report['records_scanned']=len(entries)
    for fid,needle in TARGETS.items():
        matches=[]
        for row in entries:
            name=str(row.get('fund_name') or row.get('name') or '')
            if norm(needle) in norm(name):
                matches.append({'name':name,'fund_cd':row.get('fund_cd'),'association_fund_cd':row.get('association_fund_cd'),'isin_cd':row.get('isin_cd')})
        report['candidates'][fid]=matches[:20]
except Exception as exc:
    report['status']='error'
    report['error']=str(exc)[:300]
(ROOT/'mufg_candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('MUFG discovery:',report['status'],'matches:',{k:len(v) for k,v in report['candidates'].items()})
