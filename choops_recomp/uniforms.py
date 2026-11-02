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
    original=dds.xbox_dds(cpu,gpu);out=bytearray(original);fourcc=original[84:88];bpp=8 if fourcc==b'DXT1' else 16;token=int.from_bytes(hashlib.sha256(identity.encode()).digest(),'little');bits=0
    for offset in range(128,len(out),bpp):
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


def create(workspace,model,roster_resource,team,variant,asset,template_index=None):
    if variant not in (2,3,4):raise ValueError('New uniforms use Alternate 1/2/3 slots; existing Home/Away are retained')
    if not 0<=team<len(model.rows['teams']):raise ValueError('Invalid Xbox team')
    owner=struct.unpack_from('>H',model.data,model.rows['teams'][team]['offset']+0x190)[0]
    candidates=[r for r in rows(model) if r['owner']==owner and r['variant']==0]
    if template_index is None:
        if len(candidates)!=1:raise ValueError('Choose a unique Home uniform template for this team')
        template_index=candidates[0]['index']
    template=rows(model)[template_index];updated=append(model,template_index,owner,asset,variant)
    roster_path=roster_resource.component_path()
    if sha(roster_path.read_bytes())!=sha(model.original):raise ValueError('Roster changed on disk; reopen before creating uniforms')
    marker=workspace.root/'asset_edits.json';before=marker.read_bytes() if marker.exists() else None
    registry=json.loads(before) if before else dict(version=1,platform='xbox360',edits=[],banks=[])
    registry.setdefault('banks',[]);registry.setdefault('edits',[]);plans=[];created=[];temporary=[]
    try:
        for selection in (False,True):
            source_name=name(template['asset'],template['variant'],selection);target_name=name(asset,variant,selection)
            source_hash=zlib.crc32(source_name.upper().encode())&0xffffffff;target_hash=zlib.crc32(target_name.upper().encode())&0xffffffff
            if target_hash in workspace.by_hash or any(s['name']==target_name for s in registry['banks']):raise ValueError('Uniform or selection asset already exists: '+target_name)
            if source_hash not in workspace.by_hash:raise ValueError('Required Xbox template is missing: '+source_name)
            entry,layout=workspace.by_hash[source_hash];source=workspace.safe(entry['folder']);target=workspace.assets/target_name
            if entry.get('added'):raise ValueError('Choose an original Xbox uniform template; cloning a newly added bank is not yet supported')
            if target.exists():raise ValueError('New asset folder already exists')
            temp=workspace.assets/('.studio-uniform-'+uuid.uuid4().hex);temporary.append(temp);shutil.copytree(source,temp)
            if not layout.get('blocks'):raise ValueError('New uniform requires a standard Xbox template')
            cloned=copy.deepcopy(layout);cloned['textures']=[]
            seen_components=set()
            for record in cloned['records']:
                if record['type']!=0x5c369069:continue
                components=[]
                for j,start in enumerate(record['offsets']):
                    if start==0xffffffff:continue
                    components.append(next(c for c in cloned['blocks'][j]['components'] if c['start']==start))
                if not components or len(components)>2:continue
                cpu=(temp/components[0]['path']).read_bytes();gpu=(temp/components[1]['path']).read_bytes() if len(components)==2 else None
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
                if not image.exists():image.parent.mkdir(parents=True,exist_ok=True);image.write_bytes(original)
                registry['edits'].append(dict(kind='dds',source=dict(bank=target_hash,record=record['index']),file='assets/'+target_name+'/'+relative))
            (temp/'asset.json').write_text(json.dumps(cloned,indent=2)+'\n')
            registry['banks'].append(dict(name=target_name,folder='assets/'+target_name,template=source_hash));plans.append((temp,target))
        for temp,target in plans:temp.rename(target);created.append(target)
        encoded=(json.dumps(registry,indent=2)+'\n').encode();atomic_write(marker,encoded,sha(before) if before is not None else None)
        try:atomic_write(roster_path,updated,sha(model.original))
        except Exception:
            if before is None:marker.unlink()
            else:atomic_write(marker,before,sha(encoded))
            raise
        model._commit(updated);model.original=updated
        return dict(asset=asset,variant=variant,owner=owner,folders=[str(p.name) for p in created],uniform_rows=len(rows(model)))
    except Exception:
        for folder in created:
            if folder.resolve().parent==workspace.assets and folder.name in [t.name for _,t in plans]:shutil.rmtree(folder)
        raise
    finally:
        for folder in temporary:
            if folder.exists() and folder.resolve().parent==workspace.assets and folder.name.startswith('.studio-uniform-'):shutil.rmtree(folder)
