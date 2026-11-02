"""Turn reviewed Xbox setter masks into an Xbox-only field profile."""
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace
from choops_recomp.localization import entries,literal

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--summary',required=True);p.add_argument('--audit',required=True);p.add_argument('--extend',action='store_true');a=p.parse_args()
    rows=json.loads(Path(a.summary).read_text());audit=Path(a.audit).read_text();w=Workspace(a.assets);loc=entries(w.resource('hash_bd1ab121.iff/0').blocks()[0]);fields=[];ratings=[]
    words={int(addr,16):int(value,16) for addr,value in re.findall(r'^  ([0-9a-f]{8}) ([0-9a-f]{8})',audit,re.M)}
    for row in rows:
        caption=literal(loc[int(row['key'],16)])
        if not caption:raise ValueError('Nonliteral Xbox field caption')
        setter=row['setter_code'] or '';binding=int(row['binding'],16)
        match=re.search(r'\*\((uint|undefined1) \*\)\(param_1 \+ (0x[0-9a-f]+|[0-9]+)\)',setter)
        if row.get('kind')=='rating':
            offset=re.search(r'param_1 \+ (0x[0-9a-f]+|[0-9]+)',row['code'])
            ratings.append(dict(name=caption,offset=int(offset[1],0)+16,minimum=words[binding+48],maximum=words[binding+52],getter=row['getter'],setter=row['setter'],text_id=row['key']));continue
        if not match:
            if a.extend:continue
            raise ValueError('Unrecognized Xbox setter')
        size=4 if match[1]=='uint' else 1;offset=int(match[2],0)+16
        if size==1:mask=255;shift=0
        else:
            preserve=re.findall(r'& (0x[0-9a-f]{7,8})',setter)
            if len(preserve)!=1:raise ValueError('Ambiguous Xbox preservation mask')
            mask=int(preserve[0],16)^0xffffffff;shift=(mask&-mask).bit_length()-1
            if mask>>shift & ((mask>>shift)+1):raise ValueError('Noncontiguous Xbox field mask')
        key={'Weight':'weight_lbs','Hand':'hand_code'}.get(row['name'],row['name'].lower().replace(' ','_')+'_code')
        spec=dict(key=key,name=caption,offset=offset,size=size,shift=shift,bits=(mask>>shift).bit_length(),minimum=words[binding+48],maximum=words[binding+52],getter=row['getter'],setter=row['setter'],text_id=row['key'])
        section=re.search(r'^match='+row['binding']+r'\n(.*?)(?=^  [0-9a-f]{8})',audit,re.M|re.S)
        choices={int(i):literal(loc[int(ident,16)]) for i,ident in re.findall(r'^option=(\d+) id=([0-9a-f]{8})',section[1],re.M)} if section else {}
        if choices and all(v is not None for v in choices.values()) and set(choices)==set(range(spec['maximum']+1)):spec['choices']=choices
        fields.append(spec)
    target=Path(__file__).resolve().parents[2]/'choops_recomp/data/xbox_player_fields.json'
    if a.extend:
        existing=json.loads(target.read_text());merged={f['key']:f for f in existing['fields']};merged.update({f['key']:f for f in fields});fields=list(merged.values());ratings=existing['ratings']
        if len(fields)!=33:raise ValueError('Expected all 33 native player appearance properties')
    if len(fields) not in (21,33) or len(ratings)!=30 or [r['offset'] for r in ratings]!=list(range(60,120,2)):raise ValueError('Incomplete Xbox field profile')
    target.write_text(json.dumps(dict(platform='xbox360',version=1,anchor_bias=16,fields=fields,ratings=ratings),indent=2)+'\n');print(f'Promoted {len(fields)} properties and 30 rating captions from Xbox evidence; {sum(bool(f.get("choices")) for f in fields)} native option lists')
if __name__=='__main__':main()
