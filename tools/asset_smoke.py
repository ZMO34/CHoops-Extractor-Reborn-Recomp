"""Exercise additions on a private three-bank copy, never the supplied game."""
import argparse,hashlib,json,shutil,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp.workspace import Workspace
from choops_recomp.roster import Roster
from choops_recomp import uniforms

def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',required=True);p.add_argument('--full-editor',action='store_true');a=p.parse_args();original=Workspace(a.assets);destination=Path(a.output).resolve()
    if destination.exists() or destination.is_relative_to(original.root):raise ValueError('Choose a new private output outside the supplied installation')
    roster=original.of_type('ROST')[0];model=Roster(roster.blocks()[0]);rows=uniforms.rows(model);choice=None
    import struct
    for team in model.rows['teams']:
        owner=struct.unpack_from('>H',model.data,team['offset']+0x190)[0]
        home=[r for r in rows if r['owner']==owner and r['variant']==0]
        missing=[v for v in (2,3,4) if not any(r['owner']==owner and r['variant']==v for r in rows)]
        if len(home)==1 and missing:choice=(team['index'],home[0],missing[0]);break
    if choice is None:raise ValueError('No available alternate test slot')
    team,home,variant=choice;names=[uniforms.name(home['asset'],home['variant'],s) for s in (False,True)];selected=[roster.entry]
    for name in names:selected.append(original.by_hash[zlib.crc32(name.upper().encode())&0xffffffff][0])
    destination.mkdir(parents=True);manifest=dict(original.manifest,entries=selected)
    for entry in selected:shutil.copytree(original.root/entry['folder'],destination/entry['folder'])
    (destination/'assets.json').write_text(json.dumps(manifest))
    shutil.copy2(original.root/'runtime_capabilities.json',destination/'runtime_capabilities.json')
    before={name:hashes(destination/'assets'/name) for name in names}
    w=Workspace(destination/'assets');resource=w.of_type('ROST')[0];m=Roster(resource.blocks()[0]);result=uniforms.create(w,m,resource,team,variant,900)
    reopened=Workspace(destination/'assets');reparsed=Roster(reopened.of_type('ROST')[0].blocks()[0])
    assert len(uniforms.rows(reparsed))==len(rows)+1
    assert all(before[name]==hashes(destination/'assets'/name) for name in names)
    assert all(name in reopened.banks for name in result['folders'])
    discovered=[]
    for name in result['folders']:
        layout=json.loads((destination/'assets'/name/'asset.json').read_text())
        for t in layout['textures']:discovered.append(dict(source=dict(bank=layout['identity']['hash'],record=t['record']),file='assets/'+name+'/'+t['path']))
    assert not (destination/'asset_edits.json').exists()
    for edit in discovered:
        r=next(r for r in reopened.resources if r.entry['hash']==edit['source']['bank'] and r.record['index']==edit['source']['record'])
        from choops_recomp.dds import xbox_dds,image
        blocks=r.blocks();private=xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);replacement=(destination/edit['file']).read_bytes()
        source=next(source for source in original.resources if source.entry['hash']==r.entry['template_hash'] and source.record['index']==r.record['index'])
        source_blocks=source.blocks();baseline=xbox_dds(source_blocks[0],source_blocks[1] if len(source_blocks)>1 else None)
        assert private!=baseline and image(private).tobytes()==image(baseline).tobytes()
        assert private==replacement
    assert not any(p for name in result['folders'] for p in (destination/'assets'/name).rglob('*.stored'))
    report=dict(result,discovered_textures=len(discovered),source_templates_unchanged=True,reopened_banks=len(reopened.banks),separate_registry_required=False)
    if a.full_editor:
        from choops_recomp.workspace import sha
        owner=uniforms.owner(reparsed,team)
        if len(uniforms.owners(reparsed,owner))>1:uniforms.detach(reparsed,team);reparsed.save(reopened.of_type('ROST')[0].component_path())
        current=next(r for r in uniforms.rows(reparsed) if r['owner']==uniforms.owner(reparsed,team) and r['variant']==0)
        count=len(uniforms.rows(reparsed));clone=uniforms.clone_artwork(reopened,reparsed,reopened.of_type('ROST')[0],team,current['index'],901)
        assert len(uniforms.rows(reparsed))==count and uniforms.rows(reparsed)[current['index']]['asset']==901
        uniforms.set_available(reparsed,reopened,uniforms.owner(reparsed,team),variant,False);reparsed.save(reopened.of_type('ROST')[0].component_path());assert uniforms.disabled(Roster(reopened.of_type('ROST')[0].blocks()[0]))
        uniforms.set_available(reparsed,reopened,uniforms.owner(reparsed,team),variant,True);reparsed.save(reopened.of_type('ROST')[0].component_path());assert not uniforms.disabled(Roster(reopened.of_type('ROST')[0].blocks()[0]))
        assert all(before[name]==hashes(destination/'assets'/name) for name in names)
        report.update(private_home_clone=clone['folders'],alternate_disable_restore=True,reopened_banks=len(Workspace(destination/'assets').banks))
    (destination/'smoke-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
