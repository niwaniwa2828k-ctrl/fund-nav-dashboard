#!/usr/bin/env python3
"""Fetch configured public/authorized CSV endpoints and persist NAV history.
No fabricated prices. One bad source does not erase previous records.
"""
import csv, io, json, os, pathlib, urllib.request, datetime, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
FUNDS=json.loads((ROOT/'funds.json').read_text(encoding='utf-8'))
PATH=ROOT/'data'/'nav.json'
store=json.loads(PATH.read_text(encoding='utf-8')) if PATH.exists() else {'updated_at':None,'history':{},'errors':{}}
store.setdefault('history',{});store.setdefault('errors',{})

def parse_csv(payload, fund):
    text=payload.decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text)))
    result=[]
    for r in rows:
        date=(r.get('date') or r.get('日付') or r.get('基準日') or '').strip().replace('/','-')
        value=(r.get('nav') or r.get('基準価額') or r.get('基準価額(円)') or '').replace(',','').replace('円','').strip()
        code=(r.get('code') or r.get('fund_code') or '').strip()
        if fund.get('source_code') and code != fund['source_code']:continue
        try:
            datetime.date.fromisoformat(date)
            nav=float(value)
            if nav <= 0:continue
            result.append({'date':date,'nav':nav})
        except (ValueError,TypeError):continue
    return result

ok=0
for f in FUNDS:
    url=f.get('source_url','').strip()
    if not url:
        store['errors'][f['id']]='データ提供元が未設定';continue
    if not url.startswith('https://'):
        store['errors'][f['id']]='HTTPSのURLのみ対応';continue
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'FundNavWatch/1.0 (personal dashboard)'})
        with urllib.request.urlopen(req,timeout=25) as response:
            data=response.read(8_000_001)
        if len(data)>8_000_000:raise ValueError('CSVが8MBを超えています')
        new=parse_csv(data,f)
        if not new:raise ValueError('有効な基準価額データがありません')
        merged={r['date']:r for r in store['history'].get(f['id'],[])}
        merged.update({r['date']:r for r in new})
        store['history'][f['id']]=sorted(merged.values(),key=lambda x:x['date'])
        store['errors'].pop(f['id'],None)
        ok+=1
    except Exception as e:
        store['errors'][f['id']]=str(e)[:200]
store['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
PATH.parent.mkdir(parents=True,exist_ok=True)
PATH.write_text(json.dumps(store,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Updated {ok}/{len(FUNDS)} funds; configured {sum(bool(f.get("source_url")) for f in FUNDS)}')
