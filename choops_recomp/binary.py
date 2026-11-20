"""Bounded, explicitly big-endian Xbox resource reads."""
import struct


class Binary:
    def __init__(self,data):self.data=data
    def take(self,offset,size):
        if offset<0 or size<0 or offset+size>len(self.data):raise ValueError(f'Range exceeds resource: {offset:#x}+{size:#x}')
        return self.data[offset:offset+size]
    def u32(self,offset):return struct.unpack('>I',self.take(offset,4))[0]
    def u16(self,offset):return struct.unpack('>H',self.take(offset,2))[0]
    def relative(self,field):
        delta=struct.unpack('>i',self.take(field,4))[0]
        if delta in (0,-1):raise ValueError('Null resource pointer')
        return field+delta-1
    def string(self,offset,limit=2048):
        end=offset
        for _ in range(limit):
            if self.take(end,2)==b'\0\0':return self.take(offset,end-offset).decode('utf-16-be')
            end+=2
        raise ValueError('Unterminated resource string')
