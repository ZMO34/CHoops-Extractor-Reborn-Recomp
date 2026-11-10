"""Xbox CDF-backed resource descriptors, validated against paired extents."""
from .binary import Binary


def records(metadata,data_size):
    b=Binary(metadata)
    if b.u32(0)!=0xF0985030:raise ValueError('Not Xbox paired metadata')
    end,count=b.u32(4),b.u32(24)
    if not 0x68+count*4<=end<=len(metadata) or count>100000:raise ValueError('Invalid paired metadata extent')
    table=b.relative(32);b.take(table,count*4);name=b.string(b.relative(36))
    result=[]
    for i in range(count):
        rec=b.relative(0x68+i*4);desc=b.relative(table+i*4)
        if rec+20>end or desc+16>end:raise ValueError('Paired record exceeds metadata')
        header,hl,payload,pl=(b.u32(desc+j*4) for j in range(4))
        if header+hl>data_size or payload+pl>data_size:raise ValueError('Paired resource exceeds data file')
        result.append(dict(index=i,id=b.u32(rec),type=0x5C369069 if b.u32(rec+4)==0x5C36FB69 else b.u32(rec+4),offsets=[],folder=f"_resources/{i:04d}_{b.u32(rec):08x}",ranges=[(header,hl),(payload,pl)]))
    return name,result
