"""Read-only Xbox catalog evidence. Never copies source-platform metadata."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    w=Workspace(a.assets)
    terms=['Til U Had Enough','Spit It Clearly','Hi Hi Yikas','Yea Alabama','You\'re Doing It','Time To Shine','cribmusic','fight song']
    found=[];seen=set()
    for r in w.resources:
        if r.kind=='AUDO':continue
        for c in r.components[:1]:
            if 'path' not in c:continue
            path=r.component_path()
            if path in seen or not path.is_file() or path.stat().st_size>32*1024*1024:continue
            seen.add(path);data=path.read_bytes()
            for term in terms:
                for encoding in ('ascii','utf-16-be','utf-16-le','loc-tokens'):
                    pattern=b''.join(bytes((1,ord(c))) for c in term) if encoding=='loc-tokens' else term.encode(encoding);start=0
                    while (pos:=data.lower().find(pattern.lower(),start))>=0:
                        found.append(dict(resource=r.key,term=term,encoding=encoding,offset=pos,context=data[max(0,pos-64):pos+len(pattern)+96].hex()));start=pos+len(pattern)
    Path(a.output).write_text(json.dumps(dict(platform='xbox360',matches=found),indent=2))
    print(f'{len(found)} matches in {len(seen)} Xbox components')
if __name__=='__main__':main()
