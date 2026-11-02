"""CLI for the same direct-folder operations used by the desktop editor."""
import argparse
import json
from pathlib import Path
from .workspace import Workspace
from . import audio,dds,scene,edits
from .roster import Roster
from .player_fields import FIELDS


def main(argv=None):
    p=argparse.ArgumentParser(description='Xbox recomp assets-folder editor')
    p.add_argument('--assets',type=Path,required=True);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('info')
    sub.add_parser('roster-links')
    nullable=lambda value:None if value.casefold() in ('none','unassigned') else int(value)
    s=sub.add_parser('assign-link');s.add_argument('team',type=int);s.add_argument('field',choices=('arena','conference','rival1','rival2','rival3','coach','assistant1','assistant2'));s.add_argument('target',type=nullable)
    s=sub.add_parser('move-player');s.add_argument('player',type=int);s.add_argument('team',type=nullable)
    s=sub.add_parser('move-conference');s.add_argument('team',type=int);s.add_argument('conference',type=nullable)
    s=sub.add_parser('reorder-player');s.add_argument('team',type=int);s.add_argument('player',type=int);s.add_argument('position',type=int)
    s=sub.add_parser('uniform-edit');s.add_argument('index',type=int)
    for field in ('asset','shape','variant','unlock'):s.add_argument('--'+field,type=int)
    s=sub.add_parser('uniform-available');s.add_argument('team',type=int);s.add_argument('variant',type=int,choices=(2,3,4));s.add_argument('state',choices=('on','off'))
    s=sub.add_parser('uniform-detach');s.add_argument('team',type=int)
    s=sub.add_parser('uniform-clone');s.add_argument('team',type=int);s.add_argument('index',type=int);s.add_argument('asset',type=int)
    for command in ('review-audio-folder','import-audio-folder'):
        s=sub.add_parser(command);s.add_argument('folder',type=Path)
        if command=='import-audio-folder':s.add_argument('--resources',help='Comma-separated reviewed resource keys; omitted applies all changed tracks')
    s=sub.add_parser('inspect-resource');s.add_argument('resource');s.add_argument('--component',type=int,default=0);s.add_argument('--offset',type=lambda value:int(value,0),default=0);s.add_argument('--length',type=int,default=4096)
    for command in ('export-wav','import-wav','export-dds','import-dds','import-artwork','export-cloth-obj','import-cloth-obj','export-font-atlas','import-font-atlas','scene-info'):
        s=sub.add_parser(command);s.add_argument('resource')
        if command!='scene-info':s.add_argument('file',type=Path)
    s=sub.add_parser('roster-export');s.add_argument('file',type=Path)
    s=sub.add_parser('roster-set');s.add_argument('table');s.add_argument('index',type=int);s.add_argument('field');s.add_argument('value')
    s=sub.add_parser('add-uniform');s.add_argument('team',type=int);s.add_argument('variant',type=int,choices=(2,3,4));s.add_argument('asset',type=int)
    for command in ('export-csv','compare-csv','import-csv'):
        s=sub.add_parser(command);s.add_argument('file',type=Path)
        if command=='export-csv':s.add_argument('--table',default='players')
        if command=='import-csv':s.add_argument('--fields',help='Comma-separated reviewed field keys; omitted applies all changed fields')
    args=p.parse_args(argv);w=Workspace(args.assets)
    if args.command=='info':print(json.dumps(w.report(),indent=2));return 0
    if args.command in ('roster-links','assign-link','move-player','move-conference','reorder-player','uniform-edit','uniform-available','uniform-detach','uniform-clone'):
        from . import relationships,uniforms
        resource=w.of_type('ROST')[0];model=Roster(resource.blocks()[0])
        if args.command=='roster-links':print(json.dumps(relationships.catalog(model),indent=2));return 0
        if args.command=='assign-link':relationships.assign(model,args.team,args.field,args.target)
        elif args.command=='move-player':relationships.move_player(model,args.player,args.team)
        elif args.command=='move-conference':relationships.move_conference(model,args.team,args.conference)
        elif args.command=='reorder-player':relationships.reorder_player(model,args.team,args.player,args.position)
        elif args.command=='uniform-edit':uniforms.edit(model,w,args.index,**{field:getattr(args,field) for field in ('asset','shape','variant','unlock')})
        elif args.command=='uniform-available':uniforms.set_available(model,w,uniforms.owner(model,args.team),args.variant,args.state=='on')
        elif args.command=='uniform-detach':uniforms.detach(model,args.team)
        elif args.command=='uniform-clone':print(json.dumps(uniforms.clone_artwork(w,model,resource,args.team,args.index,args.asset),indent=2));return 0
        model.save(resource.component_path());print('Checked Xbox roster relationship/uniform changes saved');return 0
    if args.command in ('review-audio-folder','import-audio-folder'):
        rows=audio.review_batch(w,args.folder)
        if args.command=='review-audio-folder':print(json.dumps(rows,indent=2));return 0
        if args.resources:
            keys=set(args.resources.split(','));available={row['resource'] for row in rows}
            if not keys<=available:raise ValueError('Requested audio resources are absent from changed-track review')
            rows=[row for row in rows if row['resource'] in keys]
        print(f'Saved {audio.apply_batch(w,args.folder,rows)} native WAV replacements');return 0
    if args.command in ('export-csv','compare-csv','import-csv'):
        from . import roster_csv
        resource=w.of_type('ROST')[0];model=Roster(resource.blocks()[0])
        if args.command=='export-csv':roster_csv.export(model,args.table,args.file);return 0
        changes=roster_csv.review(model,args.file)
        if args.command=='compare-csv':print(json.dumps(changes,indent=2));return 0
        roster_csv.apply(model,changes,set(args.fields.split(',')) if args.fields else None);model.save(resource.component_path());print('Reviewed CSV fields saved');return 0
    if args.command.startswith('roster-') or args.command=='add-uniform':
        resource=w.of_type('ROST')[0];model=Roster(resource.blocks()[0])
        if args.command=='roster-export':
            if args.file.exists():raise ValueError('Choose a new JSON destination')
            args.file.write_text(json.dumps(dict(platform='xbox360',rows=model.rows),indent=2));return 0
        if args.command=='add-uniform':
            from .uniforms import create
            print(json.dumps(create(w,model,resource,args.team,args.variant,args.asset),indent=2));return 0
        if args.table=='players' and (args.field in ('jersey_number','height_inches','position_code') or args.field in FIELDS):model.set_player(args.index,args.field,int(args.value))
        elif args.table=='conferences' and args.field not in ('name','abbreviation'):
            from .conference_history import set_value
            set_value(model,args.index,args.field,int(args.value))
        elif args.field.startswith('rating_'):model.set_rating(args.index,int(args.field[7:])-1,float(args.value))
        else:model.set_string(args.table,args.index,args.field,args.value)
        model.save(resource.component_path());print('Xbox roster saved');return 0
    resource=w.resource(args.resource)
    if args.command in ('export-font-atlas','import-font-atlas'):
        from . import uniform_fonts
        if args.command=='import-font-atlas':uniform_fonts.save_atlas(resource,args.file);print('Xbox font artwork saved directly to its component')
        else:
            if args.file.exists():raise ValueError('Choose a new font artwork destination')
            uniform_fonts.atlas(resource.blocks()).save(args.file)
    elif args.command in ('export-cloth-obj','import-cloth-obj'):
        from . import geometry
        if args.command=='export-cloth-obj':geometry.export_obj(resource,args.file);print('Source-bound Xbox cloth OBJ exported')
        else:print(f'Saved {geometry.import_obj(resource,args.file)} cloth positions directly to the resource component')
    elif args.command=='inspect-resource':
        from .inspection import page,hex_text
        print(hex_text(page(resource,args.component,args.offset,args.length),args.offset))
    elif args.command=='export-wav':print(json.dumps(audio.export_wav(resource,args.file),indent=2))
    elif args.command=='import-wav':edits.save_audio(resource,args.file);print('Native WAV saved')
    elif args.command=='scene-info':
        result=scene.preview(resource.blocks());print(json.dumps(dict(parts=len(result['meshes']),triangles=sum(len(m['vertices'])//3 for m in result['meshes']),warnings=result['warnings']),indent=2))
    elif args.command=='export-dds':
        if args.file.exists():raise ValueError('Choose a new DDS destination')
        parts=resource.blocks();args.file.write_bytes(dds.xbox_dds(parts[0],parts[1] if len(parts)>1 else None))
    elif args.command=='import-dds':edits.save_texture(resource,args.file.read_bytes());print('Native DDS saved')
    elif args.command=='import-artwork':
        parts=resource.blocks();original=dds.xbox_dds(parts[0],parts[1] if len(parts)>1 else None)
        edits.save_texture(resource,edits.artwork_payload(args.file,original));print('Native artwork DDS saved directly to resource folder')
    return 0
