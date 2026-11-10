"""Combine Xbox arena and floor records with independent material texture keys."""
import zlib
from . import scene,dds


def crc(name):return zlib.crc32(name.encode('ascii'))&0xffffffff


def available(workspace):
    result=[]
    for asset in range(1024):
        bank=crc(f'S{asset:03d}.IFF')
        if bank in workspace.by_hash:result.append(asset)
    return result


def sources(workspace,asset,mode='combined'):
    if type(asset) is not int or not 0<=asset<=1023 or mode not in ('combined','arena','floor'):raise ValueError('Choose an Xbox stadium and view mode')
    result=[]
    for role in ('arena','floor'):
        if mode!='combined' and role!=mode:continue
        candidates=[]
        for prefix in ('s','f') if role=='floor' else ('s',):
            bank=crc(f'{prefix}{asset:03d}.iff'.upper());matches=[r for r in workspace.of_type('SCNE') if r.entry['hash']==bank and r.record['id']==crc(role)]
            if len(matches)>1:raise ValueError('Ambiguous Xbox '+role+' scene')
            if matches:candidates=matches;break
        if not candidates:raise ValueError('Missing Xbox '+role+' scene for stadium '+str(asset))
        result.append((role,candidates[0]))
    return result


def preview(workspace,asset,mode='combined'):
    result=dict(meshes=[],images={},textures=[],warnings=[],declared_parts=0,resource=None,sources=[])
    for role,resource in sources(workspace,asset,mode):
        blocks=resource.blocks();decoded=scene.preview(blocks);result['sources'].append(resource.key);result['declared_parts']+=decoded['declared_parts'];result['warnings'].extend(role+': '+warning for warning in decoded['warnings'])
        try:art=scene.textures(blocks)
        except ValueError as exc:art=[];result['warnings'].append(role+' textures: '+str(exc))
        keys={}
        for texture in art:
            if 'dds' not in texture:result['warnings'].append(role+' texture '+str(texture['index'])+': '+texture.get('reason','Unsupported image'));continue
            key=resource.key+':'+str(texture['index']);path=resource.folder/f'texture_{texture["index"]:04d}.dds';descriptor=dds.info(texture['dds']);payload=path.read_bytes() if path.is_file() and 'raw_format' not in descriptor and not descriptor.get('direct_component') else texture['dds'];result['images'][key]=dds.image(payload);keys[texture['index']]=key;result['textures'].append(dict(texture,index=key,source_resource=resource,source_index=texture['index'],dds=payload,role=role))
        for mesh in decoded['meshes']:
            mesh['name']=role+'/'+mesh['name']
            for batch in mesh['batches']:batch['texture_index']=keys.get(batch.get('texture_index'))
            result['meshes'].append(mesh)
    result['warnings'].append('Combined authored geometry in source coordinates; runtime lights, animated crowds and injected passes are not reproduced.')
    return result
