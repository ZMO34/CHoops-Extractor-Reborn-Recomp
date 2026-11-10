"""CHMOD commands share the GUI authoring backend."""
import argparse
import json
from pathlib import Path
from .mod_project import ModProject,validate_archive


def main(argv=None):
    p=argparse.ArgumentParser(description='Non-destructive CHMOD authoring')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('create');s.add_argument('project',type=Path);s.add_argument('--assets',type=Path,required=True);s.add_argument('--runtime',type=Path,required=True)
    for field in ('id','name','author'):s.add_argument('--'+field,required=True)
    for name in ('add-bank','review','export','attach-roster','attach-extension','attach-uniform','metadata'):
        s=sub.add_parser(name);s.add_argument('project',type=Path)
        if name in ('export', 'attach-roster', 'attach-extension', 'attach-uniform'):
            s.add_argument('--runtime', type=Path, required=True, help='Trusted local runtime installation')
        if name=='add-bank':s.add_argument('bank')
        if name=='export':s.add_argument('output',type=Path);s.add_argument('--dependency',action='append',default=[],type=Path)
        if name=='attach-roster':s.add_argument('payload',type=Path);s.add_argument('header',type=Path)
        if name=='attach-extension':s.add_argument('dll',type=Path)
        if name=='attach-uniform':s.add_argument('folder',type=Path);s.add_argument('template_hash',type=lambda s:int(s,0))
        if name=='metadata':s.add_argument('json_file',type=Path,help='Project manifest metadata; content generated on export')
    s=sub.add_parser('inspect');s.add_argument('archive',type=Path)
    a=p.parse_args(argv)
    if a.command=='inspect':print(json.dumps(validate_archive(a.archive),indent=2));return 0
    if a.command=='create':ModProject.create(a.project,a.assets,a.runtime,a.id,a.name,a.author);return 0
    project=ModProject(a.project, getattr(a, 'runtime', None))
    if a.command=='add-bank':project.add_bank(a.bank)
    elif a.command=='review':print(json.dumps(project.review(),indent=2))
    elif a.command=='export':print(json.dumps(project.export(a.output,a.dependency),indent=2))
    elif a.command=='attach-roster':project.attach_roster(a.payload,a.header)
    elif a.command=='attach-extension':project.attach_extension(a.dll)
    elif a.command=='attach-uniform':project.attach_uniform(a.folder,a.template_hash)
    elif a.command=='metadata':
        from .mod_project import read_json
        project.state['manifest']=read_json(a.json_file);project.save()
    return 0
