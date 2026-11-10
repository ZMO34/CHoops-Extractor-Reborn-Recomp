"""Validate Xbox relationships and font authoring without editing supplied files."""
import argparse,json,struct,sys,zlib
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp.workspace import Workspace,sha
from choops_recomp.roster import Roster
from choops_recomp import relationships as links,uniforms,uniform_fonts as fonts


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();output=args.output.resolve();owned=Path(__file__).resolve().parents[1]/'output'
    if output.exists() or not output.is_relative_to(owned):raise ValueError('Choose a new private output directory under this checkout/output')
    output.mkdir(parents=True);workspace=Workspace(args.assets);resource=workspace.of_type('ROST')[0];original=resource.blocks()[0];model=Roster(original);state=links.catalog(model);operations=[]
    def check(label,operation):
        operation();links.catalog(model);model.undo()
        if bytes(model.data)!=original:raise AssertionError('Relationship undo changed source bytes')
        operations.append(label)
    for field in links.REFERENCES:check(field,lambda field=field:links.assign(model,0,field,1))
    player=state['teams'][0]['players'][0];check('transfer',lambda:links.move_player(model,player,1));check('unassign',lambda:links.move_player(model,player,None));check('lineup',lambda:links.reorder_player(model,0,player,1));check('conference-unassign',lambda:links.move_conference(model,0,None))
    lookup={(r.entry['hash'],r.record['id'],r.record['type']):r for r in workspace.resources if 'stream' not in r.record};good=0
    for row in uniforms.rows(model):
        name=uniforms.name(row['asset'],row['variant']);bank=zlib.crc32(name.upper().encode('ascii'))&0xffffffff
        for atlas,role,count in [('names','names',28),('jersey_numbers','numbers',10)]:
            target=lookup[(bank,zlib.crc32(atlas.encode())&0xffffffff,0x5c369069)];metrics=lookup[(bank,zlib.crc32(role.encode())&0xffffffff,0x68b693b2)];width=fonts.layout(target.blocks())[0];fonts.metrics(metrics.blocks(),width,count);good+=1
    target=fonts.resource(workspace,'uh000.iff','names',0x5c369069);cpu,gpu=target.blocks();path=output/'font-component.dat';path.write_bytes(gpu);private=SimpleNamespace(blocks=lambda:[cpu,path.read_bytes()],component_path=lambda index:path);image=fonts.atlas(private.blocks());image.save(output/'font-original.png');assert fonts.save_atlas(private,output/'font-original.png') is False
    image.putdata([(255-r,g,b,a) for r,g,b,a in fonts.pixels(image)]);image.save(output/'font-edited.png');fonts.save_atlas(private,output/'font-edited.png');assert fonts.atlas(private.blocks()).tobytes()==image.tobytes();assert target.blocks()==[cpu,gpu] and resource.blocks()[0]==original
    report=dict(teams=len(state['teams']),conferences=len(state['conferences']),assigned_players=len(state['schools']),relationship_operations=operations,font_pairs=good,indexed_font_exact_rgba_import=True,source_unchanged=True,game_launched=False);(output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
