"""Xbox uniform routing and additive folder creation.

All 988 supplied rows resolve with this packing to existing Xbox asset hashes.
New banks retain their template's resource structure and unknown bytes.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import uuid
import zlib
from .roster import Roster
from .workspace import sha,atomic_write
from . import dds

BANKS='haxyz'
VARIANTS=('Home','Away','Alternate 1','Alternate 2','Alternate 3')
_DORMANT=b'XRUFv001'


def disabled(model):
    """Editor-owned dormant rows; never consumed by the Xbox active table."""
    data=bytes(model.data);start=data.rfind(_DORMANT)
    if start<0:return []
    if start+12>len(data):raise ValueError('Truncated dormant uniform metadata')
    count=struct.unpack_from('>I',data,start+8)[0];end=start+12+count*8
    if count>8192 or end+32>len(data) or hashlib.sha256(data[start:end]).digest()!=data[end:end+32]:raise ValueError('Invalid dormant uniform metadata')
    return [dict(owner=a>>22&1023,asset=a>>12&1023,variant=a>>8&7,shape=b>>27&7,unlock=a&127,word0=a,word1=b) for a,b in struct.iter_unpack('>II',data[start+12:end])]


def _dormant(data,records):
    if len(records)>8192 or len({(r['owner'],r['variant']) for r in records})!=len(records):raise ValueError('Dormant uniform assignments exceed capacity or contain duplicates')
    payload=_DORMANT+struct.pack('>I',len(records))+b''.join(struct.pack('>II',r['word0'],r['word1']) for r in records);data.extend(bytes((-len(data))%4));data.extend(payload+hashlib.sha256(payload).digest())


def set_available(model,workspace,owner_id,variant,enabled):
    if variant not in (2,3,4) or type(enabled) is not bool:raise ValueError('Availability applies to alternate uniform slots')
    active=rows(model);dormant=disabled(model);selected=[r for r in active if r['owner']==owner_id and r['variant']==variant];saved=[r for r in dormant if r['owner']==owner_id and r['variant']==variant]
    if len(selected)>1 or len(saved)>1 or selected and saved:raise ValueError('Ambiguous alternate assignment')
    if bool(selected)==enabled:return
    if enabled:
        if not saved:raise ValueError('Create this alternate before enabling it')
        validate_asset(workspace,saved[0]['asset'],variant);active.append(saved[0]);dormant.remove(saved[0])
    else:
        if not selected:raise ValueError('Alternate assignment is missing')
        active.remove(selected[0]);dormant.append(selected[0])
    if not active or len(active)>8192:raise ValueError('Invalid active uniform table size')
    data=bytearray(model.data);target=(len(data)+3)&~3;data.extend(bytes(target-len(data)));data.extend(b''.join(struct.pack('>II',r['word0'],r['word1']) for r in active));struct.pack_into('>Ii',data,0x70,len(active),target-0x74+1);_dormant(data,dormant);Roster(data);model._commit(data)


def owner(model,team):
    return struct.unpack_from('>H',model.data,model.row('teams',team)['offset']+0x190)[0]


def owners(model,value):return [t['index'] for t in model.rows['teams'] if owner(model,t['index'])==value]


def validate_asset(workspace,asset,variant):
    from .uniform_preview import records
    for selection in (False,True):
        filename=name(asset,variant,selection);identity=zlib.crc32(filename.upper().encode('ascii'))&0xffffffff
        if identity not in workspace.by_hash:raise ValueError('Missing Xbox uniform folder: '+filename)
        if not selection:
            for candidates in (('unifregion','unif'),('shortregion','short')):
                found=[]
                for record_name in candidates:
                    matches=records(workspace,filename,'TXTR',record_name)
                    if len(matches)>1:raise ValueError('Ambiguous uniform artwork: '+filename)
                    if matches:found=matches;break
                if not found:raise ValueError('Missing jersey/shorts artwork in '+filename)
                blocks=found[0].blocks();dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None)


def edit(model,workspace,index,asset=None,shape=None,variant=None,unlock=None):
    current=rows(model)
    if not isinstance(index,int) or not 0<=index<len(current):raise ValueError('Invalid uniform row')
    row=current[index];asset=row['asset'] if asset is None else asset;variant=row['variant'] if variant is None else variant;shape=row['shape'] if shape is None else shape;unlock=row['unlock'] if unlock is None else unlock
    if not isinstance(shape,int) or not 0<=shape<5 or not isinstance(unlock,int) or not 0<=unlock<=127:raise ValueError('Invalid Xbox uniform shape/unlock code')
    if any(r['index']!=index and r['owner']==row['owner'] and r['variant']==variant for r in current):raise ValueError('That owner already has this uniform slot')
    if any(r['owner']==row['owner'] and r['variant']==variant for r in disabled(model)):raise ValueError('That slot has a disabled assignment; restore it first')
    validate_asset(workspace,asset,variant);data=bytearray(model.data);offset=model.row('uniforms',index)['offset'];a,b=struct.unpack_from('>II',data,offset)
    a=(a&~((1023<<12)|(7<<8)|127))|(asset<<12)|(variant<<8)|unlock;b=(b&~(7<<27))|(shape<<27);struct.pack_into('>II',data,offset,a,b);model._commit(data)


def detach(model,team):
    """Give a school private routing rows while retaining its current artwork."""
    old=owner(model,team);shared=owners(model,old)
    if len(shared)==1:return old
    current=rows(model);selected=[r for r in current if r['owner']==old]
    if not selected or len({r['variant'] for r in selected})!=len(selected):raise ValueError('Uniform owner has missing or ambiguous routing rows')
    dormant=disabled(model);occupied={owner(model,t['index']) for t in model.rows['teams']}|{r['owner'] for r in current+dormant};new=next((n for n in range(1024) if n not in occupied),None)
    if new is None or len(current)+len(selected)>8192:raise ValueError('No free uniform owner/table capacity')
    start,count,stride=model.tables['uniforms'];data=bytearray(model.data);target=(len(data)+3)&~3;data.extend(bytes(target-len(data)));data.extend(model.data[start:start+count*stride])
    for row in selected:data.extend(struct.pack('>II',(row['word0']&~(1023<<22))|(new<<22),row['word1']))
    copied=[dict(r,owner=new,word0=(r['word0']&~(1023<<22))|(new<<22)) for r in dormant if r['owner']==old]
    struct.pack_into('>Ii',data,0x70,count+len(selected),target-0x74+1);struct.pack_into('>H',data,model.row('teams',team)['offset']+0x190,new)
    if copied:_dormant(data,dormant+copied)
    model._commit(data);return new


def name(asset,variant,selection=False):
    if not 0<=asset<=1023 or not 0<=variant<5:raise ValueError('Xbox uniform selector exceeds supported range')
    return ('sel' if selection else '')+'u'+BANKS[variant]+f'{asset:03d}.iff'


def rows(model):
    start,count,stride=model.tables['uniforms'];result=[]
    for i in range(count):
        a,b=struct.unpack_from('>II',model.data,start+i*stride)
        result.append(dict(index=i,owner=a>>22&1023,asset=a>>12&1023,variant=a>>8&7,shape=b>>27&7,unlock=a&127,word0=a,word1=b))
    return result


def append(model,template,owner,asset,variant):
    current=rows(model)
    if not 0<=template<len(current) or not 0<=owner<=1023:raise ValueError('Invalid Xbox uniform template/owner')
    name(asset,variant)
    if any(r['owner']==owner and r['variant']==variant for r in disabled(model)):raise ValueError('This alternate is disabled; enable the existing assignment instead')
    if any(r['owner']==owner and r['variant']==variant for r in current):raise ValueError('That owner already has this uniform variant; existing rows are not replaced')
    if len(current)>=8192:raise ValueError('Uniform table limit reached')
    start,count,stride=model.tables['uniforms'];table=bytes(model.data[start:start+count*stride]);a,b=current[template]['word0'],current[template]['word1']
    a=(a&~((1023<<22)|(1023<<12)|(7<<8)|127))|(owner<<22)|(asset<<12)|(variant<<8)
    target=(len(model.data)+3)&~3;data=bytearray(model.data);data.extend(b'\0'*(target-len(data)));data.extend(table);data.extend(struct.pack('>II',a,b))
    struct.pack_into('>I',data,0x70,count+1);struct.pack_into('>i',data,0x74,target-0x74+1)
    parsed=Roster(data)
    if bytes(parsed.data[target:target+len(table)])!=table:raise ValueError('Existing uniform rows changed')
    return bytes(data)


def _private_image(cpu,gpu,identity):
    """Give copied BC data its own identity without changing any decoded pixel.

    Endpoint permutations in four-color BC blocks are exactly equivalent after
    remapping selectors. This prevents a clone's native DDS from affecting its
    source bank, whose original content identity must remain untouched.
    """
    original=dds.xbox_dds(cpu,gpu);out=bytearray(original);fourcc=original[84:88];bpp=next(size for code,size in dds.FORMATS.values() if code==fourcc);token=int.from_bytes(hashlib.sha256(identity.encode()).digest(),'little')|1;bits=0
    for offset in range(128,len(out),8 if fourcc in (b'ATI1',b'ATI2') else bpp):
        if fourcc in (b'ATI1',b'ATI2'):
            selectors=int.from_bytes(out[offset+2:offset+8],'little');codes=[selectors>>(3*i)&7 for i in range(16)];equal=out[offset]==out[offset+1]
            eligible=[i for i,code in enumerate(codes) if code in (0,1)]
            if not eligible or not equal and len(eligible)!=16:continue
            if token>>bits&1:
                if equal:selectors^=1<<(3*eligible[0])
                else:
                    out[offset],out[offset+1]=out[offset+1],out[offset];selectors^=sum(1<<(3*i) for i in range(16))
                out[offset+2:offset+8]=selectors.to_bytes(6,'little')
            bits+=1
            if bits==64:break
            continue
        color=offset+(0 if bpp==8 else 8);selectors=int.from_bytes(out[color+4:color+8],'little')
        if bpp==8 and selectors&0xaaaaaaaa:continue
        if token>>bits&1:
            out[color:color+4]=out[color+2:color+4]+out[color:color+2]
            out[color+4:color+8]=(selectors^0x55555555).to_bytes(4,'little')
        bits+=1
        if bits==64:break
    if bits<16 or out==original:raise ValueError('This BC image cannot obtain a verified independent identity')
    if dds.image(original).tobytes()!=dds.image(out).tobytes():raise ValueError('Independent texture encoding changed decoded pixels')
    a,b,dimension=struct.unpack_from('>3I',cpu,0x94);width=(dimension&8191)+1;pitch=((a>>22)&511)*8;endian=(b>>6)&3
    source=bytearray(cpu if gpu is None else gpu)
    base=0x6c+struct.unpack_from('>i',cpu,0x6c)[0]-1 if gpu is None else struct.unpack_from('>I',cpu,0x6c)[0]-1
    for n,offset in enumerate(range(128,len(out),bpp)):
        if out[offset:offset+bpp]==original[offset:offset+bpp]:continue
        x,y=n%((width+3)//4),n//((width+3)//4)
        target=base+(dds.tiled_offset(x,y,pitch,bpp.bit_length()-1) if a>>31 else (y*pitch+x)*bpp)
        block=out[offset:offset+bpp];source[target:target+bpp]=bytes(block[i^(0,1,3,2)[endian]] for i in range(bpp))
    check=dds.xbox_dds(bytes(source) if gpu is None else cpu,None if gpu is None else bytes(source))
    if check!=out:raise ValueError('Xbox private encoding failed round trip')
    return bytes(source),original


def create(workspace,model,roster_resource,team,variant,asset,template_index=None,replace_index=None):
    workspace.require('added_asset_banks')
    workspace.require('direct_resources')
    if replace_index is None and variant not in (2,3,4):raise ValueError('New uniforms use Alternate 1/2/3 slots; existing Home/Away are retained')
    if not 0<=team<len(model.rows['teams']):raise ValueError('Invalid Xbox team')
    owner=struct.unpack_from('>H',model.data,model.rows['teams'][team]['offset']+0x190)[0]
    candidates=[r for r in rows(model) if r['owner']==owner and r['variant']==0]
    if template_index is None:
        if len(candidates)!=1:raise ValueError('Choose a unique Home uniform template for this team')
        template_index=candidates[0]['index']
    template=rows(model)[template_index]
    if replace_index is not None:
        if replace_index!=template_index or template['owner']!=owner or template['variant']!=variant:raise ValueError('Private artwork clone must retain the selected school and uniform slot')
        if len(owners(model,owner))!=1:raise ValueError('Make this school routing independent before cloning its artwork')
        name(asset,variant);updated=bytearray(model.data);offset=model.row('uniforms',replace_index)['offset'];a=struct.unpack_from('>I',updated,offset)[0];struct.pack_into('>I',updated,offset,(a&~(1023<<12))|(asset<<12));updated=bytes(updated)
    else:updated=append(model,template_index,owner,asset,variant)
    roster_path=roster_resource.component_path()
    if sha(roster_path.read_bytes())!=sha(model.original):raise ValueError('Roster changed on disk; reopen before creating uniforms')
    if workspace.manifest.get('storage')!='loose-resources':raise ValueError('Finish the direct-folder migration before adding assets')
    plans=[];created=[];temporary=[]
    try:
        for selection in (False,True):
            source_name=name(template['asset'],template['variant'],selection);target_name=name(asset,variant,selection)
            source_hash=zlib.crc32(source_name.upper().encode())&0xffffffff;target_hash=zlib.crc32(target_name.upper().encode())&0xffffffff
            if target_hash in workspace.by_hash:raise ValueError('Uniform or selection asset already exists: '+target_name)
            if source_hash not in workspace.by_hash:raise ValueError('Required Xbox template is missing: '+source_name)
            entry,layout=workspace.by_hash[source_hash];source=workspace.safe(entry['folder']);target=workspace.assets/target_name
            if target.exists():raise ValueError('New asset folder already exists')
            temp=workspace.assets/('.studio-uniform-'+uuid.uuid4().hex);temporary.append(temp);shutil.copytree(source,temp,ignore=shutil.ignore_patterns('*.stored'))
            if not layout.get('blocks'):raise ValueError('New uniform requires a standard Xbox template')
            cloned=copy.deepcopy(layout);cloned['textures']=[]
            flags=entry.get('toc_flags',workspace.manifest['loader_metadata']['toc_flags'].get(str(entry.get('template_hash',source_hash))))
            if flags is None:raise ValueError('Missing Xbox loader metadata for template')
            cloned['identity']=dict(name=target_name,hash=target_hash,source_size=entry['size'],toc_flags=flags,template_hash=source_hash)
            seen_components=set()
            for record in cloned['records']:
                if record['type']!=0x5c369069:continue
                components=[]
                for j,start in enumerate(record['offsets']):
                    if start==0xffffffff:continue
                    components.append(next(c for c in cloned['blocks'][j]['components'] if c['start']==start))
                if not components or len(components)>2:continue
                cpu=(temp/components[0]['path']).read_bytes();gpu=(temp/components[1]['path']).read_bytes() if len(components)==2 else None
                try:source_image=dds.xbox_dds((source/components[0]['path']).read_bytes(),(source/components[1]['path']).read_bytes() if len(components)==2 else None)
                except ValueError:continue
                component=components[1] if gpu is not None else components[0];key=component['path']
                if key not in seen_components:
                    try:dds.xbox_dds(cpu,gpu)
                    except ValueError:continue
                    # A supported image must obtain a verified private identity.
                    # Failing here is essential: falling back to a shared source
                    # identity would let the clone change the original uniform.
                    private,original=_private_image(cpu,gpu,target_name+':'+key)
                    (temp/key).write_bytes(private);seen_components.add(key)
                else:
                    original=dds.xbox_dds(cpu,gpu)
                relative=record['folder']+'/texture.dds';image=temp/relative
                current_cpu=(temp/components[0]['path']).read_bytes();current_gpu=(temp/components[1]['path']).read_bytes() if len(components)==2 else None
                private_image=dds.xbox_dds(current_cpu,current_gpu)
                if not image.exists() or image.read_bytes()==source_image:
                    image.parent.mkdir(parents=True,exist_ok=True);image.write_bytes(private_image)
                info=dds.info(private_image);fmt=next(fmt for fmt,(code,size) in dds.FORMATS.items() if code==private_image[84:88])
                cloned['textures'].append(dict(path=relative,record=record['index'],sha256=sha(private_image),identity=dds.fnv64(private_image[128:]),descriptor=dict(width=info['width'],height=info['height'],format=fmt)))
            (temp/'asset.json').write_text(json.dumps(cloned,indent=2)+'\n')
            plans.append((temp,target))
        for temp,target in plans:temp.rename(target);created.append(target)
        atomic_write(roster_path,updated,sha(model.original))
        model._commit(updated);model.original=updated
        return dict(asset=asset,variant=variant,owner=owner,folders=[str(p.name) for p in created],uniform_rows=len(rows(model)))
    except Exception:
        for folder in created:
            if folder.resolve().parent==workspace.assets and folder.name in [t.name for _,t in plans]:shutil.rmtree(folder)
        raise
    finally:
        for folder in temporary:
            if folder.exists() and folder.resolve().parent==workspace.assets and folder.name.startswith('.studio-uniform-'):shutil.rmtree(folder)


def clone_artwork(workspace,model,roster_resource,team,index,asset):
    if type(index) is not int or not 0<=index<len(rows(model)):raise ValueError('Invalid uniform row')
    row=rows(model)[index]
    return create(workspace,model,roster_resource,team,row['variant'],asset,template_index=index,replace_index=index)
