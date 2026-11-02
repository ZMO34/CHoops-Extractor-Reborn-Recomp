"""Direct Xbox assets-folder model. No disc/archive/staging adapters."""
from dataclasses import dataclass,field
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zlib

TYPES={0xE26C9B5D:'SCNE',0x5C369069:'TXTR',0xC61649B2:'ROST',0x1AEDDA1F:'AUDO'}


def sha(data):return hashlib.sha256(data).hexdigest()


def atomic_write(path,data,expected=None):
    path=Path(path)
    if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):raise ValueError('Linked asset files are not writable')
    before=path.read_bytes() if path.exists() else None
    if expected is not None and (before is None or sha(before)!=expected):raise ValueError('Asset changed on disk; reopen before saving')
    fd,name=tempfile.mkstemp(prefix='.studio-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


@dataclass
class Resource:
    workspace:object
    bank:str
    entry:dict
    record:dict
    layout:dict
    components:list=field(default_factory=list)
    @property
    def kind(self):return TYPES.get(self.record['type'],f"{self.record['type']:08x}")
    @property
    def key(self):return f"{self.bank}/{self.record['index']}"
    @property
    def folder(self):return self.workspace.safe(self.entry['folder']+'/'+self.record['folder'])
    @property
    def label(self):return f"{self.bank} / {self.record['id']:08x}"
    def blocks(self):
        result=[]
        for c in self.components:
            if 'file' in c:
                with self.workspace.safe(c['file']).open('rb') as stream:
                    stream.seek(c['offset']);data=stream.read(c['size'])
                if len(data)!=c['size']:raise ValueError('Paired resource changed or was truncated')
                result.append(data)
            else:result.append(self.workspace.safe(self.entry['folder']+'/'+c['path']).read_bytes())
        return result
    def component_path(self,index=0):return self.workspace.safe(self.entry['folder']+'/'+self.components[index]['path'])


class StreamResource(Resource):
    @property
    def kind(self):return 'AUDO'
    @property
    def key(self):return super().key+':'+str(self.record['stream'])
    @property
    def label(self):
        from .audio_catalog import metadata
        info=metadata(self)
        if info:return f"{info['title']} — {info['artist']} / {self.record['stream_bank']}:{self.record['stream']}"
        return f"{self.record['stream_bank']} / track {self.record['stream']+1:04d}"
    def blocks(self):
        import struct
        c=self.components[0]
        with self.workspace.safe(c['file']).open('rb') as stream:stream.seek(c['offset']);encoded=stream.read(c['size'])
        header=struct.pack('>11I',1,5,self.record['playback_format'],self.record['samples'],self.record['sample_rate'],0,len(encoded),0,32,0,0)
        return [header,encoded]


class Workspace:
    def __init__(self,assets,progress=None):
        assets=Path(assets).resolve()
        if assets.name.casefold()!='assets':raise ValueError('Open the installed game assets folder, not a disc or individual file')
        self.assets=assets;self.root=assets.parent
        self.manifest=json.loads((self.root/'assets.json').read_text(encoding='utf-8'))
        if self.manifest.get('version')!=1 or self.manifest.get('platform')!='xbox360':raise ValueError('An Xbox recomp folder installation is required')
        from .runtime_protocol import augment_manifest
        self.manifest=augment_manifest(self.root,self.manifest)
        self.resources=[];self.banks={};self._by_key={}
        self.by_hash={};self.labels={}
        self.warnings=[]
        for n,entry in enumerate(self.manifest['entries']):
            folder=self.safe(entry['folder'])
            if folder.parent!=self.assets:raise ValueError('Asset bank lies outside assets folder')
            layout=json.loads((folder/'asset.json').read_text(encoding='utf-8'))
            self.banks[folder.name]=(entry,layout)
            self.by_hash[entry['hash']]=(entry,layout)
            for record in layout.get('records',[]):
                components=[]
                for j,start in enumerate(record['offsets']):
                    if start==0xFFFFFFFF:continue
                    matches=[c for c in layout['blocks'][j]['components'] if c['start']==start]
                    if len(matches)!=1:raise ValueError('Ambiguous or absent resource component')
                    components.append(dict(matches[0],block=j))
                resource=Resource(self,folder.name,entry,record,layout,components)
                self.resources.append(resource);self._by_key[resource.key]=resource
            if progress and n%50==0:progress(n,len(self.manifest['entries']),folder.name)
        from .cdf import records
        for bank,(entry,layout) in self.banks.items():
            if 'blocks' in layout:continue
            path=self.safe(entry['folder']+'/payload.dat')
            with path.open('rb') as stream:prefix=stream.read(4)
            if prefix!=bytes.fromhex('f0985030'):continue
            try:
                metadata=path.read_bytes();b=__import__('choops_recomp.binary',fromlist=['Binary']).Binary(metadata)
                name=b.string(b.relative(36));paired=self.banks.get(name)
                if not paired:paired=self.by_hash.get(zlib.crc32(name.upper().encode('ascii'))&0xffffffff)
                if not paired:raise ValueError('Paired Xbox data bank not found: '+name)
                data_file=paired[0]['folder']+'/payload.dat'
                _,items=records(metadata,self.safe(data_file).stat().st_size)
                for record in items:
                    components=[dict(file=data_file,offset=off,size=size) for off,size in record['ranges']]
                    resource=Resource(self,bank,entry,record,layout,components)
                    self.resources.append(resource);self._by_key[resource.key]=resource
            except (ValueError,OSError) as exc:self.warnings.append(bank+': '+str(exc))
        import struct,math
        for resource in list(self.resources):
            if resource.record['type']!=0x61df2234:continue
            try:
                data=resource.blocks()[0];b=__import__('choops_recomp.binary',fromlist=['Binary']).Binary(data)
                name=b.string(0,32);bank=self.by_hash.get(zlib.crc32(name.upper().encode('ascii'))&0xffffffff)
                if not bank:raise ValueError('Stream bank filename is not present in Xbox assets')
                path=bank[0]['folder']+'/payload.dat';data_size=self.safe(path).stat().st_size
                count,rate,fmt=b.u32(64),b.u32(76),b.u32(84)
                if not 0<count<=100000 or fmt not in (2,5) or not 1000<=rate<=192000:raise ValueError('Unsupported Xbox streaming table')
                b.take(88,(count+1)*8)
                offsets=[b.u32(92+i*8) for i in range(count+1)]
                if offsets!=sorted(offsets) or offsets[-1]>data_size:raise ValueError('Stream extents exceed bank')
                for i in range(count):
                    seconds=struct.unpack_from('>f',data,96+i*8)[0];size=offsets[i+1]-offsets[i]
                    if not math.isfinite(seconds) or not seconds>0 or not size or size%2048:raise ValueError('Unsupported Xbox stream duration/packet extent')
                    record=dict(resource.record,stream=i,stream_bank=name,playback_format=fmt,samples=round(seconds*rate),sample_rate=rate,folder=resource.record['folder']+f'/audio/track_{i:05d}')
                    child=StreamResource(self,resource.bank,resource.entry,record,resource.layout,[dict(file=path,offset=offsets[i],size=size)])
                    self.resources.append(child);self._by_key[child.key]=child
            except (ValueError,OSError) as exc:self.warnings.append(resource.label+': '+str(exc))
    def safe(self,relative):
        path=(self.root/relative).resolve()
        if not path.is_relative_to(self.assets):raise ValueError('Resource path escapes assets folder')
        return path
    def of_type(self,kind):return [r for r in self.resources if r.kind==kind]
    def resource(self,key):return self._by_key[key]
    def report(self):return dict(platform='xbox360',banks=len(self.banks),resources={kind:len(self.of_type(kind)) for kind in TYPES.values()})
