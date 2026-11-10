"""Read-only Xbox scene/texture coverage audit; private reports contain no assets."""
import argparse,collections,json,struct,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp.workspace import Workspace
from choops_recomp import scene,dds

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',required=True);p.add_argument('--scenes',action='store_true');p.add_argument('--textures',action='store_true');a=p.parse_args();start=time.monotonic();w=Workspace(a.assets);report=dict(platform='xbox360',workspace=w.report(),warnings=w.warnings,scenes=[],texture_formats={},texture_failures=[])
    if a.scenes:
        resources=w.of_type('SCNE')
        for i,r in enumerate(resources):
            try:
                result=scene.preview(r.blocks());item=dict(resource=r.key,label=r.label,parts=len(result['meshes']),declared=result['declared_parts'],triangles=sum(len(m['vertices'])//3 for m in result['meshes']),warnings=result['warnings'])
            except (ValueError,IndexError,struct.error,OverflowError) as exc:item=dict(resource=r.key,label=r.label,error=str(exc))
            report['scenes'].append(item)
            if i%100==0:print(f'SCNE {i}/{len(resources)}',flush=True)
    if a.textures:
        formats=collections.Counter();resources=w.of_type('TXTR')
        for i,r in enumerate(resources):
            blocks=r.blocks();fmt=struct.unpack_from('>I',blocks[0],0x98)[0]&63 if len(blocks[0])>=0x9c else 'short';formats[fmt]+=1
            try:dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None)
            except ValueError as exc:report['texture_failures'].append(dict(resource=r.key,format=fmt,reason=str(exc)))
            if i%500==0:print(f'TXTR {i}/{len(resources)}',flush=True)
        report['texture_formats']=dict(formats)
    report['elapsed_seconds']=round(time.monotonic()-start,2);Path(a.output).write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(scene_count=len(report['scenes']),scene_errors=sum('error' in r or bool(r.get('warnings')) for r in report['scenes']),texture_formats=report['texture_formats'],texture_failures=len(report['texture_failures']),seconds=report['elapsed_seconds'])),flush=True)
if __name__=='__main__':main()
