"""Find additional property caption IDs in Xbox localization itself."""
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace
from choops_recomp.localization import entries,literal
from choops_recomp.player_fields import FIELDS

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',required=True);a=p.parse_args();w=Workspace(a.assets);loc=entries(w.resource('hash_bd1ab121.iff/0').blocks()[0]);found=[]
    wanted={name.casefold() for name in ('Hairstyle','Hair Color','Beard Style','Sideburns','Left Shoulder','Right Shoulder','Left Biceps','Right Biceps','Left Forearm','Right Forearm','Post','Freethrow','Class','Redshirt','Redshirt Used','Scholarship','Shoe Style','Shoe Manuf.','Home Shoe Color','Away Shoe Color','Jump Shot','Close Shot Tendency','Midrange Shot Tendency','3PT Shot Tendency','Drive Tendency')}
    existing={int(field['text_id'],16) for field in FIELDS.values()}
    for key,tokens in loc.items():
        text=literal(tokens)
        if text and (text.casefold() in wanted or key in existing):found.append(dict(key=f'{key:08x}',text_id=f'0x{key:08x}',name=text))
    path=Path(a.output);path.write_text('\n'.join(r['key'] for r in found)+'\n');path.with_suffix('.json').write_text(json.dumps(found,indent=2));print('\n'.join(r['key']+' '+r['name'] for r in found))
if __name__=='__main__':main()
