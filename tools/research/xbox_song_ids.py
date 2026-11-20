"""Match candidate song titles to Xbox localization; output only Xbox evidence."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace
from choops_recomp.localization import entries,literal

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--candidates',required=True);p.add_argument('--output',required=True);a=p.parse_args();w=Workspace(a.assets)
    titles=json.loads(Path(a.candidates).read_text())['tracks'];known={r['title'].casefold():r for r in titles};found=[]
    for r in w.resources:
        if r.kind=='AUDO' or not r.components or 'path' not in r.components[0]:continue
        path=r.component_path()
        with path.open('rb') as f:magic=f.read(4)
        if magic!=bytes.fromhex('e33e3b9c'):continue
        for key,tokens in entries(path.read_bytes()).items():
            text=literal(tokens)
            if text and text.casefold() in known:
                candidate=known[text.casefold()];found.append(dict(title=text,key=f'{key:08x}',resource=r.key,candidate_index=candidate['index']))
    Path(a.output).write_text(json.dumps(found,indent=2));print(f'{len(found)} title-ID matches confirmed in Xbox localization')
if __name__=='__main__':main()
