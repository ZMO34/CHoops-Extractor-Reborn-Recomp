"""Source-bound OBJ checks on private copies of all identified Xbox cloth."""
import argparse,json,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp.workspace import Workspace,sha
from choops_recomp import geometry


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    root=args.output.resolve();owned=Path(__file__).resolve().parents[1]/'output'
    if root.exists() or not root.is_relative_to(owned):raise ValueError('Choose a new private output under this checkout/output')
    root.mkdir(parents=True);workspace=Workspace(args.assets);passed=[];unsupported=[]
    for resource in workspace.of_type('SCNE'):
        name=workspace.labels.get(resource.entry['hash'],'')
        if not name.startswith('cloth_'):continue
        original=resource.blocks()[0];folder=root/f'{resource.entry["hash"]:08x}_{resource.record["index"]}';folder.mkdir();target=folder/'component.dat';target.write_bytes(original)
        private=SimpleNamespace(key=resource.key,blocks=lambda target=target:[target.read_bytes()],component_path=lambda target=target:target)
        try:
            spec=geometry.export_obj(private,folder/'cloth.obj');geometry.import_obj(private,folder/'cloth.obj')
            if target.read_bytes()!=original:raise AssertionError('OBJ round trip changed original bytes')
            obj=folder/'cloth.obj';lines=obj.read_text().splitlines();index=next(i for i,line in enumerate(lines) if line.startswith('v '));vertex=lines[index].split();vertex[1]=format(float(vertex[1])+.01,'.9g');lines[index]=' '.join(vertex);obj.write_text('\n'.join(lines)+'\n');geometry.import_obj(private,obj)
            edited=target.read_bytes();changes=[i for i,(a,b) in enumerate(zip(original,edited)) if a!=b]
            if not changes or len(changes)>4 or len(edited)!=len(original):raise AssertionError('Position edit changed unexpected bytes')
            if sha(resource.blocks()[0])!=sha(original):raise AssertionError('Supplied source changed')
            passed.append(dict(bank=name,resource=resource.key,vertices=sum(spec['counts']),faces=len(spec['faces']),changed_bytes=len(changes)))
        except ValueError as exc:unsupported.append(dict(bank=name,resource=resource.key,reason=str(exc)))
    report=dict(passed=passed,unsupported=unsupported,game_launched=False);(root/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(dict(passed=len(passed),unsupported=unsupported),indent=2))


if __name__=='__main__':main()
