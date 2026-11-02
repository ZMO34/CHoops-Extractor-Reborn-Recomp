"""Xbox ROST profile: dynamic table pointers, 316-byte player records.

Only Xbox corpus-validated structure is exposed. Packed appearance fields and
named rating semantics are deliberately absent until Xbox consumers are traced.
"""
import struct
from contextlib import contextmanager
from .binary import Binary
from .workspace import sha,atomic_write
from .player_fields import FIELDS,RATINGS

TABLES={'players':(8,17,316,65535),'arenas':(0x20,25,28,8192),'teams':(0x28,49,704,8192),'coaches':(0x38,21,44,65535),'conferences':(0xa8,1,2964,1024),'uniforms':(0x70,1,8,8192)}
STRINGS={'players':{'last_name':0x10,'first_name':0x14},'teams':{'short_name':0x30,'abbreviation':0x34,'school_name':0x38,'mascot_plural':0x3c,'mascot_name':0x40},'coaches':{'name':0x14,'abbreviation':0x18},'arenas':{'name':0x18,'city':0x1c,'code':0x20},'conferences':{'name':0,'abbreviation':4}}


class Roster:
    def __init__(self,data):
        self.original=bytes(data);self.data=bytearray(data);self.history=[];self.redo_stack=[];self.tables={};self.rows={};self._batch=False;self.reload()
    def reload(self):
        b=Binary(self.data);self.tables={};self.rows={};self.errors=[]
        for table,(field,bias,stride,limit) in TABLES.items():
            count=b.u32(field);start=field+4+struct.unpack_from('>i',self.data,field+4)[0]-bias
            if not 0<count<=limit:raise ValueError(f'Invalid Xbox {table} count')
            b.take(start,count*stride);self.tables[table]=(start,count,stride);rows=[]
            for i in range(count):
                off=start+i*stride;row=dict(index=i,offset=off)
                for name,delta in STRINGS.get(table,{}).items():
                    try:row[name]=self.read_string(off+delta)
                    except ValueError as exc:self.errors.append((table,i,name,str(exc)));row[name]=''
                if table=='players':
                    row.update(jersey_number=self.data[off+0x1b],height_inches=self.data[off+0x3a],position_code=self.data[off+0x3b],ratings=[b.u16(off+0x3c+j*2)/100 for j in range(30)])
                    for key,field in FIELDS.items():row[key]=(int.from_bytes(b.take(off+field['offset'],field['size']),'big')>>field['shift'])&((1<<field['bits'])-1)
                if table=='teams':row['palette']=[b.take(off+0x1a0+j*4,4).hex().upper() for j in range(31)]
                if table=='uniforms':
                    a,c=b.u32(off),b.u32(off+4)
                    row.update(owner=a>>22&1023,asset=a>>12&1023,variant=a>>8&7,shape=c>>27&7,unlock=a&127)
                rows.append(row)
            self.rows[table]=rows
        if self.errors:raise ValueError(f'Xbox roster profile mismatch: {len(self.errors)} invalid string references')
    def read_string(self,field):
        delta=struct.unpack_from('>i',self.data,field)[0]
        if delta in (0,-1):return ''
        return Binary(self.data).string(field+delta-1)
    def _commit(self,changed):
        if self._batch:self.data=bytearray(changed);return
        validated=Roster(changed)
        self.history.append(bytes(self.data));self.history=self.history[-32:];self.redo_stack.clear();self.data=bytearray(validated.data);self.reload()
    @contextmanager
    def transaction(self):
        if self._batch:raise ValueError('Nested roster transactions are not supported')
        before=bytes(self.data);self._batch=True
        try:
            yield self
            changed=bytes(self.data);Roster(changed)
        except BaseException:
            self.data=bytearray(before);self.reload();raise
        finally:self._batch=False
        self.data=bytearray(before)
        if changed!=before:self._commit(changed)
    def row(self,table,index):
        if table not in self.rows or not isinstance(index,int) or not 0<=index<len(self.rows[table]):raise ValueError('Invalid Xbox roster row')
        return self.rows[table][index]
    def set_string(self,table,index,field,text):
        if field not in STRINGS.get(table,{}):raise ValueError('Unsupported Xbox string field')
        if not isinstance(text,str) or '\0' in text or any(ord(c)<32 for c in text):raise ValueError('Invalid roster text')
        row=self.row(table,index);offset=row['offset']+STRINGS[table][field];encoded=text.encode('utf-16-be')+b'\0\0'
        changed=bytearray(self.data)
        current=struct.unpack_from('>i',changed,offset)[0]
        target=offset+current-1 if current not in (0,-1) else None
        # Preserve shared strings: use original capacity only when no other
        # pointer field targets it; otherwise allocate a new owned string.
        users=sum(1 for t,rows in self.rows.items() for r in rows for name,delta in STRINGS.get(t,{}).items() if struct.unpack_from('>i',self.data,r['offset']+delta)[0] not in (0,-1) and r['offset']+delta+struct.unpack_from('>i',self.data,r['offset']+delta)[0]-1==target)
        old= self.read_string(offset).encode('utf-16-be')+b'\0\0' if target is not None else b''
        if target is not None and users==1 and len(encoded)<=len(old):changed[target:target+len(old)]=encoded+b'\0'*(len(old)-len(encoded))
        else:
            target=(len(changed)+1)&~1;changed.extend(b'\0'*(target-len(changed)));changed.extend(encoded);struct.pack_into('>i',changed,offset,target-offset+1)
        self._commit(changed)
    def set_palette(self,index,slot,rgba):
        if not 0<=slot<31 or len(rgba)!=4:raise ValueError('Palette requires a valid slot and four RGBA bytes')
        changed=bytearray(self.data);offset=self.row('teams',index)['offset']+0x1a0+slot*4;changed[offset:offset+4]=rgba;self._commit(changed)
    def set_rating(self,index,channel,value):
        if not 0<=channel<30 or not isinstance(value,(int,float)) or not RATINGS[channel]['minimum']<=value<=RATINGS[channel]['maximum']:raise ValueError('Rating channel/value outside Xbox menu range')
        changed=bytearray(self.data);struct.pack_into('>H',changed,self.row('players',index)['offset']+0x3c+channel*2,round(value*100));self._commit(changed)
    def set_player(self,index,field,value):
        if field in FIELDS:
            spec=FIELDS[field]
            if not isinstance(value,int) or not spec['minimum']<=value<=spec['maximum']:raise ValueError('Player value outside Xbox menu range')
            changed=bytearray(self.data);offset=self.row('players',index)['offset']+spec['offset'];size=spec['size'];word=int.from_bytes(changed[offset:offset+size],'big');mask=((1<<spec['bits'])-1)<<spec['shift']
            changed[offset:offset+size]=((word&~mask)|(value<<spec['shift'])).to_bytes(size,'big');self._commit(changed);return
        fields={'jersey_number':(0x1b,0,100),'height_inches':(0x3a,36,100),'position_code':(0x3b,0,4)}
        if field not in fields:raise ValueError('Unsupported Xbox player field')
        delta,lo,hi=fields[field]
        if not isinstance(value,int) or not lo<=value<=hi:raise ValueError('Player value outside supported range')
        changed=bytearray(self.data);changed[self.row('players',index)['offset']+delta]=value;self._commit(changed)
    def set_uniform(self,index,field,value):
        fields={'asset':(0,12,10,1023),'shape':(4,27,3,4)}
        if field not in fields:raise ValueError('Uniform owner, variant and unlock require a checked assignment operation')
        delta,shift,bits,maximum=fields[field]
        if not isinstance(value,int) or not 0<=value<=maximum:raise ValueError('Uniform value outside supported range')
        changed=bytearray(self.data);offset=self.rows['uniforms'][index]['offset']+delta
        word=struct.unpack_from('>I',changed,offset)[0];mask=((1<<bits)-1)<<shift
        struct.pack_into('>I',changed,offset,(word&~mask)|(value<<shift));self._commit(changed)
    def undo(self):
        if self.history:self.redo_stack.append(bytes(self.data));self.data=bytearray(self.history.pop());self.reload()
    def redo(self):
        if self.redo_stack:self.history.append(bytes(self.data));self.data=bytearray(self.redo_stack.pop());self.reload()
    def save(self,path):
        Roster(self.data);atomic_write(path,bytes(self.data),sha(self.original));self.original=bytes(self.data)
