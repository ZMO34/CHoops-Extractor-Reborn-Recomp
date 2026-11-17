"""Publish only Xbox-derived catalog metadata after localization validation."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace
from choops_recomp.localization import entries,literal

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--audit',required=True);a=p.parse_args();data=json.loads(Path(a.audit).read_text());rows=data['tracks']
    if data['platform']!='xbox360' or len(rows)!=87 or set(r['index'] for r in rows)!=set(range(87)):raise ValueError('Incomplete Xbox song audit')
    w=Workspace(a.assets);localized=entries(w.resource('hash_bd1ab121.iff/0').blocks()[0])
    for row in rows:
        if literal(localized[int(row['title_id'],16)])!=row['title']:raise ValueError('Xbox native/localized title mismatch: '+row['title'])
    if sum(r['category']=='Licensed Music' for r in rows)!=23:raise ValueError('Unexpected Xbox catalog categories')
    data['version']=1;data['evidence']='Xbox native tables cross-checked with all 87 Xbox localization IDs';data['tracks']=sorted(rows,key=lambda r:r['index'])
    target=Path(__file__).resolve().parents[2]/'choops_recomp/data/xbox_jukebox.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(data,indent=2)+'\n')
    print('Published 87 Xbox-verified song identities')
if __name__=='__main__':main()
