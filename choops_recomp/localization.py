"""Xbox localization tokens: dynamic table offset, big-endian tagged text."""
from .binary import Binary


def entries(data):
    b=Binary(data)
    if b.u32(0)!=0xe33e3b9c:raise ValueError('Unsupported Xbox localization header')
    count=b.u32(4);table=b.relative(8)
    if not 0<count<=1000000 or table<12 or table%8:raise ValueError('Unsupported Xbox localization table')
    b.take(table,count*8);end=table+count*8;result={};previous=-1
    for i in range(count):
        field=table+i*8;key=b.u32(field)
        if key<=previous:raise ValueError('Localization keys are not sorted uniquely')
        previous=key
        if key==0xffffffff:continue
        target=b.relative(field+4)
        if not end<=target<len(data) or target%2:raise ValueError('Invalid localization token pointer')
        stop=target
        while b.take(stop,2)!=bytes(2):stop+=2
        result[key]=b.take(target,stop-target)
    return result


def literal(tokens):
    if len(tokens)%2 or any(tokens[i]!=1 for i in range(0,len(tokens),2)):return None
    return ''.join(chr(tokens[i+1]) for i in range(0,len(tokens),2))
