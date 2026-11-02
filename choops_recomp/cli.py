"""CLI for the same direct-folder operations used by the desktop editor."""
import argparse
import json
from pathlib import Path
from .workspace import Workspace
from . import audio,dds,scene,edits
from .roster import Roster


def main(argv=None):
    p=argparse.ArgumentParser(description='Xbox recomp assets-folder editor')
    p.add_argument('--assets',type=Path,required=True);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('info')
    for command in ('export-wav','import-wav','export-dds','import-dds','scene-info'):
        s=sub.add_parser(command);s.add_argument('resource')
        if command!='scene-info':s.add_argument('file',type=Path)
    s=sub.add_parser('roster-export');s.add_argument('file',type=Path)
    s=sub.add_parser('roster-set');s.add_argument('table');s.add_argument('index',type=int);s.add_argument('field');s.add_argument('value')
    s=sub.add_parser('add-uniform');s.add_argument('team',type=int);s.add_argument('variant',type=int,choices=(2,3,4));s.add_argument('asset',type=int)
    args=p.parse_args(argv);w=Workspace(args.assets)
    if args.command=='info':print(json.dumps(w.report(),indent=2));return 0
    if args.command.startswith('roster-') or args.command=='add-uniform':
        resource=w.of_type('ROST')[0];model=Roster(resource.blocks()[0])
        if args.command=='roster-export':
            if args.file.exists():raise ValueError('Choose a new JSON destination')
            args.file.write_text(json.dumps(dict(platform='xbox360',rows=model.rows),indent=2));return 0
        if args.command=='add-uniform':
            from .uniforms import create
            print(json.dumps(create(w,model,resource,args.team,args.variant,args.asset),indent=2));return 0
        if args.field in ('jersey_number','height_inches','position_code'):model.set_player(args.index,args.field,int(args.value))
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
    return 0
