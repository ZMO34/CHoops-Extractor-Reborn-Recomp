"""Read only CPU descriptors and GPU extents to inventory Xbox texture support."""
import argparse,collections,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp.workspace import Workspace
from choops_recomp.runtime_protocol import decode_component
from choops_recomp import raw_texture,uniform_fonts,dds


def component(resource,c,header=False):
    w=resource.workspace
    if 'file' in c:
        path=w.safe(c['file'])
        with path.open('rb') as stream:stream.seek(c['offset']);data=stream.read(c['size'] if header else min(20,c['size']))
        if header:return decode_component(data)
        return int.from_bytes(data[4:8],'big') if data[:4] in (b'ZLIB',bytes.fromhex('0e4837c3')) else c['size']
    path=w.safe(c.get('folder',resource.entry['folder'])+'/'+c['path'])
    return path.read_bytes() if header else path.stat().st_size


class Extent:
    def __init__(self,size):self.size=size
    def __len__(self):return self.size


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',required=True);p.add_argument('--pixels',action='store_true');args=p.parse_args();workspace=Workspace(args.assets);counts=collections.Counter();failures=[];formats=collections.Counter()
    for number,r in enumerate(workspace.of_type('TXTR')):
        try:
            cpu=component(r,r.components[0],True);gpu=Extent(component(r,r.components[1])) if len(r.components)>1 else None
            if len(cpu)<172:raise ValueError('Truncated CPU descriptor')
            a,b,size,f,lod,dim=struct.unpack_from('>6I',cpu,0x94);fmt=b&63;formats[fmt]+=1
            if cpu[8:12]==bytes.fromhex('24820002'):
                uniform_fonts.layout([cpu,gpu]);counts['indexed']+=1
                if args.pixels:uniform_fonts.atlas(r.blocks())
            elif fmt in dds.FORMATS:
                if a&3!=2 or dim>>9&3!=1 or b&1024 or size>>26:raise ValueError('BC dimension/stack unsupported')
                packed=dim&2048 and min((size&8191)+1,(size>>13&8191)+1)<=16;counts['BC_packed' if packed else 'BC']+=1
                if packed and args.pixels:blocks=r.blocks();dds.image(dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None))
            else:
                info=raw_texture.describe(cpu,gpu);counts['raw_cube' if info['faces']==6 else 'raw_2d']+=1
                if args.pixels:
                    blocks=r.blocks();payload=raw_texture.export_dds(blocks[0],blocks[1] if len(blocks)>1 else None)
                    for face in range(info['faces']):raw_texture.image_from_dds(payload,face)
        except (ValueError,OSError,KeyError,TypeError) as exc:failures.append(dict(resource=r.key,error=str(exc)))
        if number%500==0:print(f'TXTR {number}',flush=True)
    report=dict(counts=dict(counts),formats=dict(formats),failures=failures,scope='Descriptors plus non-BC/indexed/packed-base pixel decode' if args.pixels else 'Descriptor and extent validation; pixel round trips are separate',game_launched=False);Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
