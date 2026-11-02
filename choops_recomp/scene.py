"""Xbox SCNE geometry/material preview, bounded against supplied components.

Adapted from the owner's v1.23 preview algorithm. Xbox declarations are Xenos
formats, texture descriptors are 224 bytes, and vertex count is at descriptor+8.
No platform-specific shader or appearance assumptions are imported.
"""
import math
import struct
from .binary import Binary
from .dds import xbox_dds

VERTEX={57:'3f',37:'2f',38:'4f',36:'f',31:'2e',32:'4e',25:'2h',26:'4h',6:'4B'}


def instances(head):
    count=head.u32(0x3c)
    if not count:return {}
    if count>10000:raise ValueError('Instance table exceeds limit')
    table=head.relative(0x40);candidates=[]
    for stride in (144,128):
        try:
            head.take(table,count*stride);candidate={}
            for i in range(count):
                off=table+i*stride;matrix=struct.unpack('>16f',head.take(off,64))
                if not all(math.isfinite(v) and abs(v)<1e8 for v in matrix) or any(abs(matrix[k])>1e-5 for k in (3,7,11)) or abs(matrix[15]-1)>1e-5:raise ValueError('Invalid homogeneous transform')
                candidate.setdefault(head.u32(off+68),[]).append(matrix)
            if candidate not in candidates:candidates.append(candidate)
        except ValueError:continue
    if len(candidates)!=1:raise ValueError('Unsupported or ambiguous instance table')
    return candidates[0]


def transform(vertices,matrix):
    if matrix is None:return vertices
    return [tuple(sum(v[k]*matrix[k*4+j] for k in range(3))+matrix[12+j] for j in range(3))+tuple(v[3:]) for v in vertices]


def textures(blocks):
    if len(blocks)!=2:raise ValueError('Embedded Xbox textures require CPU and GPU components')
    head=Binary(blocks[0]);count=head.u32(0x20)
    if count>4096:raise ValueError('Texture table exceeds limit')
    table=head.relative(0x24) if count else 0;head.take(table,count*224)
    result=[]
    for i in range(count):
        off=table+i*224
        item=dict(index=i,id=head.u32(off),header_offset=off)
        try:item['dds']=xbox_dds(head.take(off,224),blocks[1])
        except ValueError as exc:item['reason']=str(exc)
        result.append(item)
    return result


def _materials(head):
    result={};tc,sc,mc=(head.u32(o) for o in (0x20,0x28,0x30))
    if tc>4096 or sc>256 or mc>10000:raise ValueError('Material tables exceed limits')
    tt=head.relative(0x24) if tc else 0;st=head.relative(0x2c) if sc else 0;mt=head.relative(0x38) if mc and head.u32(0x38) else 0
    head.take(tt,tc*224);head.take(st,sc*48)
    if not mt:return result
    head.take(mt,mc*40)
    ids={}
    for i in range(tc):ids.setdefault(head.u32(tt+i*224),[]).append(i)
    shaders={head.u32(st+i*48):st+i*48 for i in range(sc)}
    for i in range(mc):
        off=mt+i*40;s=shaders.get(head.u32(off+8));item=dict(texture_index=None)
        if s is None:continue
        uniforms,samplers=head.u32(s+8)>>16,head.u32(s+8)&65535;length=head.u32(s+12)&65535
        if uniforms>256 or samplers>32 or not length:continue
        params=head.relative(off+32);head.take(params,length)
        sampler_table=head.relative(s+28) if samplers else 0;head.take(sampler_table,samplers*36)
        for j in range(samplers):
            sampler=sampler_table+j*36;semantic=head.u32(sampler)
            if semantic not in (0xb6e7ae40,0x49412c54):continue
            ref=head.u16(sampler+16)+12
            if ref+4<=length:
                matches=ids.get(head.u32(params+ref),[])
                if len(matches)==1:item['texture_index']=matches[0];break
        ut=head.relative(s+24) if uniforms else 0;head.take(ut,uniforms*44)
        for j in range(uniforms):
            uniform=ut+j*44
            if head.u32(uniform)!=0x9015351f:continue
            offset=params+head.u16(uniform+20)
            if offset+16>params+length:raise ValueError('Color exceeds material parameter buffer')
            color=struct.unpack('>4f',head.take(offset,16))
            if all(math.isfinite(x) and 0<=x<=1 for x in color):item.update(color=color,color_offset=offset)
        result[i]=item
    return result


def preview(blocks,triangle_limit=400000):
    if not 1<=len(blocks)<=2:raise ValueError('SCNE requires one or two components')
    head=Binary(blocks[0]);gpu=head if len(blocks)==1 else Binary(blocks[1]);head.take(0,0x54)
    count=head.u32(0x44)
    if count>4096:raise ValueError('Mesh table exceeds limit')
    table=head.relative(0x48) if count else 0;head.take(table,count*176)
    warnings=[];meshes=[];total=0;transforms=instances(head)
    try:materials=_materials(head)
    except ValueError as exc:materials={};warnings.append('Materials: '+str(exc))
    for i in range(count):
        name=f'part_{i}';part=table+i*176
        try:
            name=head.string(head.relative(part))
            runs=head.u32(part+0x7c)
            if not runs:continue
            if head.u32(part+0x84)!=1 or not 1<=runs<=10000:raise ValueError('Unsupported vertex descriptor/draw count')
            desc=head.relative(part+0x88);vertices=head.u32(desc+8);streams_count=head.u32(desc+12)>>16
            if not 1<=vertices<=250000 or not 1<=streams_count<=16:raise ValueError('Invalid Xbox vertex buffer dimensions')
            streams=[]
            for j in range(streams_count):
                entry=desc+24+j*16;stride,length=head.u32(entry+4),head.u32(entry+8)
                if not 1<=stride<=256 or vertices*stride!=length:raise ValueError('Vertex buffer length differs from stride/count')
                start=head.relative(entry+12) if len(blocks)==1 else head.u32(entry+12)-1
                streams.append((stride,gpu.take(start,length)))
            n=head.u32(part+0x98);decl=head.relative(part+0x9c)
            if not 1<=n<=32:raise ValueError('Unsupported declaration count')
            head.take(decl,n*64);attributes=[]
            for j in range(n):
                off=decl+j*64;code=head.take(off+8,8);fmt=int.from_bytes(code[4:],'big')&63
                if code[0] not in (0x20,0x30) or code[2]>=streams_count or fmt not in VERTEX:continue
                attributes.append(dict(offset=code[1],stream=code[2],format=fmt,index=code[3],semantic=head.u32(off),quantized=code[0]==0x30,bias=struct.unpack('>4f',head.take(off+16,16)),scale=struct.unpack('>4f',head.take(off+32,16))))
            positions=[a for a in attributes if a['offset']==0 and a['index']==0 and a['format'] in (57,26,38)]
            if len(positions)!=1:raise ValueError('Unsupported/ambiguous position declaration')
            position=positions[0]
            # Xenos float/half two-component declarations in supplied meshes are
            # UV channels; retain explicit ambiguity instead of guessing a slot.
            uvs=[a for a in attributes if a['format'] in (31,37,25) and a['index']==0]
            uv=uvs[-1] if uvs else None
            colors=[a for a in attributes if a not in positions and a['format'] in (38,32) and a['index']==0]
            color=colors[0] if len(colors)==1 else None
            def value(a,vertex):
                stride,data=streams[a['stream']];fmt='>'+VERTEX[a['format']]
                if a['offset']+struct.calcsize(fmt)>stride:raise ValueError('Declaration exceeds vertex stride')
                v=struct.unpack_from(fmt,data,vertex*stride+a['offset'])
                if a['format'] in (25,26):
                    v=tuple(max(-1.,x/32767.) for x in v)
                    if a['quantized']:v=tuple(x*a['scale'][k]+a['bias'][k] for k,x in enumerate(v))
                if not all(math.isfinite(x) and abs(x)<1e8 for x in v):raise ValueError('Invalid vertex values')
                return v
            points=[]
            for vertex in range(vertices):
                xyz=value(position,vertex)[:3];tex=value(uv,vertex)[:2] if uv else (0.,0.);rgba=value(color,vertex) if color else (1.,1.,1.,1.)
                points.append((*xyz,*tex,*rgba))
            flags=head.u32(part+0xa4)
            if flags&0xffff!=16 or flags&~0x30010010:raise ValueError(f'Unsupported Xbox index flags {flags:#x}')
            indices_count=head.u32(part+0xa8)
            if indices_count>2000000:raise ValueError('Index buffer exceeds limit')
            start=head.relative(part+0xac) if len(blocks)==1 else head.u32(part+0xac)-1
            indices=struct.unpack('>'+str(indices_count)+'H',gpu.take(start,indices_count*2))
            draw=head.relative(part+0x80);candidates=[]
            for stride in (48,64):
                try:
                    head.take(draw,runs*stride)
                    if all(head.u32(draw+j*stride)==6 and head.u32(draw+j*stride+4)+head.u32(draw+j*stride+8)<=indices_count for j in range(runs)):candidates.append(stride)
                except ValueError:pass
            if not candidates or len(candidates)>1 and runs>1:raise ValueError('Unsupported/ambiguous draw layout')
            stride=candidates[0];triangles=[];batches=[]
            for j in range(runs):
                run=draw+j*stride;first,size=head.u32(run+4),head.u32(run+8);strip=[];before=len(triangles)
                for index in indices[first:first+size]:
                    if index==65535:strip=[];continue
                    if index>=vertices:raise ValueError('Index outside vertex buffer')
                    strip.append(index)
                    if len(strip)>=3:
                        a,b,c=strip[-3:]
                        if len(strip)%2==0:a,b=b,a
                        if len({a,b,c})==3:triangles.extend((points[a],points[b],points[c]))
                mat=head.u32(run+32) if stride==48 else head.u16(run+32)
                batches.append(dict(first=before,count=len(triangles)-before,material=mat,**materials.get(mat,dict(texture_index=None))))
                if total+len(triangles)>triangle_limit*3:raise ValueError('Preview triangle budget exceeded')
            if triangles:
                for matrix in transforms.get(head.u32(part+4),[None]):
                    if total+len(triangles)>triangle_limit*3:raise ValueError('Instanced preview triangle budget exceeded')
                    total+=len(triangles);meshes.append(dict(name=name,vertices=transform(triangles,matrix),batches=batches,hidden_by_default='roof' in name.lower() or 'light_fx' in name.lower()))
        except (ValueError,struct.error) as exc:warnings.append(name+': '+str(exc))
    return dict(meshes=meshes,warnings=warnings,materials=materials,declared_parts=count)
