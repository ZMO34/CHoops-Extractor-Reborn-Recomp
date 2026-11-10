"""Standalone Xbox shoe mesh with explicit authored upper/sole material names."""
import zlib
from . import scene,dds
from .uniform_preview import unique

CANDIDATES=[f'shoe_{i}.iff' for i in range(2)]+[f'shoe_{base+style}_{color:02d}.iff' for base in (100,200,300,500) for style in range(4) for color in range(16)]

def available(workspace):return [name for name in CANDIDATES if zlib.crc32(name.upper().encode())&0xffffffff in workspace.by_hash]

def preview(workspace,filename):
    if filename not in available(workspace):raise ValueError('Choose existing Xbox shoe artwork')
    identity=zlib.crc32(b'hi_shoe1')&0xffffffff;meshes=[r for r in workspace.of_type('SCNE') if r.record['id']==identity]
    if len(meshes)!=1:raise ValueError('Standalone Xbox shoe SCNE identity is missing or ambiguous')
    result=scene.preview(meshes[0].blocks());result.update(images={},textures=[],resource=None)
    for index,role in enumerate(('shoe_upper','shoe_sole')):
        r=unique(workspace,filename,'TXTR',role);blocks=r.blocks();edited=r.folder/'texture.dds';payload=edited.read_bytes() if edited.is_file() else dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None)
        image=dds.image(payload);image.putalpha(255);result['images'][index]=image
    upper={'fastener_mat','midsole_mat','toe_mat','heel_mat','logo_mat','hitop_mat','upper_mat'}
    for mesh in result['meshes']:
        # Stock shoe COLOR0 is black while the runtime shoe shader supplies its
        # lighting/material response. The artwork preview uses neutral lighting.
        mesh['vertices']=[(*vertex[:5],1.,1.,1.,1.) for vertex in mesh['vertices']]
        for batch in mesh['batches']:
            name=batch.get('material_name')
            if name=='sole_mat':batch['texture_index']=1
            elif name in upper:batch['texture_index']=0
            else:result['warnings'].append('Unmapped Xbox shoe material: '+str(name))
    result['warnings'].append('Authored static shoe silhouette; artwork selection does not alter the underlying mesh.')
    return result
