"""Native-recomp DDS editing: retain BC format, permit larger artwork."""
import io
import struct
from PIL import Image
from .workspace import atomic_write,sha

FORMATS={18:(b'DXT1',8),19:(b'DXT3',16),20:(b'DXT5',16)}


def info(data):
    if len(data)<128 or data[:4]!=b'DDS ' or struct.unpack_from('<I',data,4)[0]!=124:raise ValueError('Invalid DDS')
    height,width=struct.unpack_from('<II',data,12);mips=max(1,struct.unpack_from('<I',data,28)[0]);fourcc=data[84:88]
    if fourcc not in [x[0] for x in FORMATS.values()] or not 1<=width<=8192 or not 1<=height<=8192 or width%4 or height%4:raise ValueError('Supported native DDS: 2D BC1/BC2/BC3, at most 8192 pixels')
    if struct.unpack_from('<I',data,112)[0] or struct.unpack_from('<I',data,24)[0]>1:raise ValueError('Only 2D DDS is supported')
    if mips>max(width,height).bit_length():raise ValueError('DDS mip count exceeds dimensions')
    bpp=8 if fourcc==b'DXT1' else 16
    expected=sum(((max(1,width>>i)+3)//4)*((max(1,height>>i)+3)//4)*bpp for i in range(mips))
    if len(data)!=128+expected:raise ValueError('DDS payload does not match its mip chain')
    return dict(width=width,height=height,mips=mips,fourcc=fourcc.decode())


def image(data):
    info(data)
    with Image.open(io.BytesIO(data)) as source:return source.convert('RGBA')


def replace(path,payload,baseline=None):
    old=path.read_bytes();a=info(baseline or old);b=info(payload)
    scale=b['width']//a['width']
    if a['fourcc']!=b['fourcc'] or b['width']<a['width'] or b['width']%a['width'] or b['width']*a['height']!=b['height']*a['width'] or not scale or scale&(scale-1):raise ValueError('Keep BC format/aspect ratio; native power-of-two upscales are supported. No downsizing is performed.')
    image(payload)
    atomic_write(path,payload,sha(old))
    return b


def fnv64(data):
    value=14695981039346656037
    for x in data:value=((value^x)*1099511628211)&0xFFFFFFFFFFFFFFFF
    return f'{value:016x}'


def tiled_offset(x,y,pitch,log_bpp):
    pitch=(pitch+31)&~31;macro=((x>>5)+(y>>5)*(pitch>>5))<<(log_bpp+7)
    micro=((x&7)+((y&14)<<2))<<log_bpp;o=macro+((micro&~15)<<1)+(micro&15)+((y&1)<<4)
    return ((o&~511)<<3)+((y&16)<<7)+((o&448)<<2)+(((((y&8)>>2)+(x>>3))&3)<<6)+(o&63)


def xbox_dds(cpu,gpu=None,base=None):
    if len(cpu)<0xAC:raise ValueError('Truncated Xbox TXTR')
    a,b,size,_,lod,dim=struct.unpack_from('>6I',cpu,0x94);fmt=b&63
    width,height=(size&8191)+1,((size>>13)&8191)+1
    if a&3!=2 or fmt not in FORMATS or (dim>>9)&3!=1 or size>>26 or b&0x400 or width%4 or height%4 or (dim&0x800 and min(width,height)<=16):raise ValueError(f'Unsupported Xbox base texture layout/format {fmt}')
    source=cpu if gpu is None else gpu
    start=(0x6c+struct.unpack_from('>i',cpu,0x6c)[0]-1) if gpu is None else struct.unpack_from('>I',cpu,0x6c)[0]-1
    if base is not None:start=base
    length=struct.unpack_from('>I',cpu,0x70)[0];pitch=((a>>22)&511)*8
    if start<0 or start+length>len(source) or pitch*4<width:raise ValueError('Xbox texture payload exceeds its component')
    fourcc,bpp=FORMATS[fmt];out=bytearray();endian=(b>>6)&3
    for y in range((height+3)//4):
        for x in range((width+3)//4):
            offset=tiled_offset(x,y,pitch,bpp.bit_length()-1) if a>>31 else (y*pitch+x)*bpp
            if offset+bpp>length:raise ValueError('Tiled address exceeds texture payload')
            block=source[start+offset:start+offset+bpp]
            out.extend(block[i^(0,1,3,2)[endian]] for i in range(bpp))
    header=bytearray(128);header[:4]=b'DDS ';struct.pack_into('<7I',header,4,124,0x81007,height,width,len(out),0,1)
    struct.pack_into('<II4s',header,76,32,4,fourcc);struct.pack_into('<I',header,108,0x1000)
    return bytes(header)+out
