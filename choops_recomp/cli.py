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
    for command in ('export-wav','import-wav','export-dds','import-dds','import-artwork','scene-info'):
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
        if args.field in ('jersey_number','height_inches','position_code') or args.field in FIELDS:model.set_player(args.index,args.field,int(args.value))
        elif args.field.startswith('rating_'):model.set_rating(args.index,int(args.field[7:])-1,float(args.value))
        else:model.set_string(args.table,args.index,args.field,args.value)
        model.save(resource.component_path());print('Xbox roster saved');return 0
    resource=w.resource(args.resource)
    if args.command=='export-wav':print(json.dumps(audio.export_wav(resource,args.file),indent=2))
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
