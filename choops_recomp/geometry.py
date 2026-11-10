"""Source-bound OBJ position editing for verified Xbox embedded cloth streams."""
import json,math,struct
from pathlib import Path
from . import scene
from .workspace import sha,atomic_write


def source(resource):
    blocks=resource.blocks()
    if len(blocks)!=1:raise ValueError('OBJ position editing currently supports embedded Xbox cloth only')
    result=scene.preview(blocks,source_geometry=True)
    if result['warnings'] or not result['source_meshes'] or len(result['source_meshes'])!=result['declared_parts']:raise ValueError('OBJ editing requires all source meshes to decode without warnings')
    if any(m['position']['format']!=57 or m['position']['quantized'] for m in result['source_meshes']):raise ValueError('OBJ editing requires verified float3 position streams')
    return blocks[0],result['source_meshes']


def export_obj(resource,path):
    path=Path(path);marker=path.with_suffix(path.suffix+'.json')
    if path.exists() or marker.exists():raise ValueError('Choose a new OBJ destination')
    data,meshes=source(resource);lines=['# Xbox embedded cloth; preserve vertex order and face indices'];base=1;faces=[];counts=[]
    for index,mesh in enumerate(meshes):
        lines.append(f'o xbox_mesh_{index}');counts.append(len(mesh['points']))
        for point in mesh['points']:lines.append('v '+' '.join(format(v,'.9g') for v in point[:3]))
        for point in mesh['points']:lines.append('vt '+' '.join(format(v,'.9g') for v in point[3:5]))
        for i in range(0,len(mesh['indices']),3):
            face=[base+j for j in mesh['indices'][i:i+3]];faces.append(face);lines.append('f '+' '.join(f'{v}/{v}' for v in face))
        base+=len(mesh['points'])
    spec=dict(version=1,platform='xbox360',resource=resource.key,source_sha256=sha(data),counts=counts,faces=faces,operation='float3-positions-only',coordinates='source-model-space')
    atomic_write(marker,(json.dumps(spec,indent=2)+'\n').encode('utf-8'))
    try:atomic_write(path,('\n'.join(lines)+'\n').encode('ascii'))
    except BaseException:marker.unlink();raise
    return spec


def import_obj(resource,path):
    path=Path(path);marker=path.with_suffix(path.suffix+'.json')
    if marker.stat().st_size>64*1024*1024:raise ValueError('OBJ companion exceeds the cloth import limit')
    spec=json.loads(marker.read_text(encoding='utf-8'));data,meshes=source(resource)
    if spec.get('version')!=1 or spec.get('platform')!='xbox360' or spec.get('resource')!=resource.key or spec.get('source_sha256')!=sha(data) or spec.get('operation')!='float3-positions-only':raise ValueError('OBJ companion does not match this Xbox resource; export again')
    counts=[len(m['points']) for m in meshes]
    if spec.get('counts')!=counts:raise ValueError('OBJ source mesh counts changed')
    vertices=[];faces=[]
    if path.stat().st_size>64*1024*1024:raise ValueError('OBJ exceeds the cloth import limit')
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        fields=line.split()
        if not fields or fields[0].startswith('#'):continue
        if fields[0]=='v':
            if len(fields)!=4:raise ValueError('OBJ positions require exactly three coordinates')
            vertex=tuple(float(v) for v in fields[1:])
            if not all(math.isfinite(v) and abs(v)<1e6 for v in vertex):raise ValueError('Invalid OBJ position')
            vertices.append(vertex)
        elif fields[0]=='f':
            if len(fields)!=4:raise ValueError('Preserve triangulated OBJ topology')
            faces.append([int(v.split('/')[0]) for v in fields[1:]])
        elif fields[0] not in ('vt','vn','o','g','s','usemtl','mtllib'):raise ValueError('Unsupported OBJ statement: '+fields[0])
    if len(vertices)!=sum(counts) or faces!=spec['faces']:raise ValueError('Preserve OBJ vertex order/count and exact face indices')
    # Recompute topology from the live source; companion files are not trusted.
    expected=[];base=1
    for mesh in meshes:
        for i in range(0,len(mesh['indices']),3):expected.append([base+j for j in mesh['indices'][i:i+3]])
        base+=len(mesh['points'])
    if faces!=expected:raise ValueError('OBJ topology differs from the Xbox source')
    result=bytearray(data);cursor=0;patches={}
    for mesh in meshes:
        for i in range(len(mesh['points'])):
            offset=mesh['stream_start']+i*mesh['stride']+mesh['position']['offset'];payload=struct.pack('>3f',*vertices[cursor]);cursor+=1
            if offset in patches and patches[offset]!=payload:raise ValueError('Conflicting shared position edits')
            patches[offset]=payload
    for offset,payload in patches.items():result[offset:offset+12]=payload
    if scene.preview([bytes(result)])['warnings']:raise ValueError('Edited Xbox cloth failed preview validation')
    atomic_write(resource.component_path(),bytes(result),sha(data));return len(vertices)
