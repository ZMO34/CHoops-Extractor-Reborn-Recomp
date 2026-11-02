"""Authored Xbox cloth and uniform artwork, resolved by verified CRC identities."""
import zlib
from . import scene,dds,uniforms

SHAPES=('u','v','vtri','tri','wishbone')

def records(workspace,filename,kind,record_name):
    bank=zlib.crc32(filename.upper().encode('ascii'))&0xffffffff;identity=zlib.crc32(record_name.encode('ascii'))&0xffffffff
    return [r for r in workspace.of_type(kind) if r.entry['hash']==bank and r.record['id']==identity]

def unique(workspace,filename,kind,record_name):
    matches=records(workspace,filename,kind,record_name)
    if len(matches)!=1:raise ValueError('Xbox asset identity missing or ambiguous: '+filename+'/'+record_name)
    return matches[0]

def preview(workspace,row,shape=None,build='reg',shorts='reg',number=None,surname=''):
    if shape is None:shape=row['shape']
    if not 0<=shape<5 or build not in ('thin','reg','fat') or shorts not in ('thin','reg','fat'):raise ValueError('Unsupported Xbox cloth shape')
    filename=uniforms.name(row['asset'],row['variant']);result=dict(meshes=[],images={},textures=[],warnings=[],declared_parts=0,resource=None)
    for texture_index,(role,bank,record_name,art_names) in enumerate((('jersey',f'cloth_{SHAPES[shape]}_{build}.iff',f'jersey_{SHAPES[shape]}_{build}',('unifregion','unif')),('shorts','cloth_shorts.iff',f'shorts{shorts}',('shortregion','short')))):
        garment=unique(workspace,bank,'SCNE',record_name);art=None
        for art_name in art_names:
            matches=records(workspace,filename,'TXTR',art_name)
            if len(matches)>1:raise ValueError('Ambiguous Xbox uniform artwork')
            if matches:art=matches[0];break
        if art is None:raise ValueError('Missing Xbox '+role+' artwork')
        edited=art.folder/'texture.dds';blocks=art.blocks();payload=edited.read_bytes() if edited.is_file() else dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None)
        image=dds.image(payload);image.putalpha(255);result['images'][texture_index]=image
        decoded=scene.preview(garment.blocks());result['declared_parts']+=decoded['declared_parts'];result['warnings'].extend(decoded['warnings'])
        for mesh in decoded['meshes']:
            mesh['name']=role+'/'+mesh['name']
            for batch in mesh['batches']:batch.update(texture_index=texture_index,color=(1.,1.,1.,1.))
            result['meshes'].append(mesh)
    if number is not None or surname:
        from . import uniform_fonts as fonts
        transforms,name_placement,name_scale=fonts.placement(workspace)
        if number is not None:
            image,metrics=fonts.glyphs(workspace,filename,'numbers');result['images']['__number']=fonts.number_image(image,metrics,number,fonts.template(workspace,'jerseynum00'))
        if surname:
            image,metrics=fonts.glyphs(workspace,filename,'names');result['images']['__name']=fonts.name_image(image,metrics,surname,fonts.template(workspace,'jerseyname00'))
        for mesh in result['meshes']:
            if not mesh['name'].startswith('jersey/'):continue
            for batch in mesh['batches']:
                if number is not None:batch.update(number_texture='__number',number_uv=transforms[0],back_number_uv=transforms[1])
                if surname:batch.update(name_texture='__name',name_placement=name_placement,name_scale=name_scale)
    result['warnings'].append('Authored static cloth and glyph artwork; runtime skinning, cloth simulation and player body are not reproduced.')
    return result
