"""Check direct DDS substitution on a generated private fixture, never the game."""
import argparse,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp.workspace import Workspace
from choops_recomp.edits import save_texture

def main():
    p=argparse.ArgumentParser();p.add_argument('--recomp',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);a=p.parse_args();root=a.fixture.resolve();project=Path(__file__).resolve().parents[1]
    if not root.is_relative_to(project/'output') or not (root/'smoke-report.json').is_file():raise ValueError('Use a private fixture created by asset_smoke.py under this project output directory')
    sys.path.insert(0,str(a.recomp.resolve()/'tools'));from prepare_direct_assets import prepare_direct
    before=prepare_direct(root);w=Workspace(root/'assets');targets=[r for r in w.of_type('TXTR') if r.entry.get('added')];resource=targets[0]
    components={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'assets').rglob('block*.dat')}
    target=resource.folder/'texture.dds';payload=bytearray(target.read_bytes());payload[128]^=1;save_texture(resource,payload)
    after=prepare_direct(root);bindings=(root/'native_dds.index').read_text().splitlines()[1:]
    assert len([row for row in bindings if row])==1
    assert before['segments']==after['segments']
    assert components=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'assets').rglob('block*.dat')}
    assert not (root/'_cache').exists()
    print('One direct DDS binding; resource bodies and direct-read map unchanged; no archive or asset-cache binaries built.')
if __name__=='__main__':main()
