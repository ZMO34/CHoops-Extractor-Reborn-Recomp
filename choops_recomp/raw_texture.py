"""Lossless base-plane editing for Xbox uncompressed and half-float textures.

Edits touch individual loose GPU/CPU components, never an assembled IFF. DDS
retains native precision; image import retains dimensions and untouched texels.
"""
import math,struct
from pathlib import Path
from PIL import Image
from .dds import tiled_offset
from .workspace import atomic_write,sha

FORMATS={2:1,4:2,6:4,10:2,31:4,32:8}
DXGI={10:49,31:34,32:10}


def describe(cpu,gpu=None):
    if len(cpu)<224:raise ValueError('Truncated Xbox texture descriptor')
    a,b,size,filtering,lod,dimension=struct.unpack_from('>6I',cpu,0x94);fmt=b&63;kind=dimension>>9&3;fallback=fmt==0
    code=struct.unpack_from('>I',cpu,8)[0]
    if fallback:
        fmt=code&63;packed=struct.unpack_from('>I',cpu,0x60)[0];width,height=packed>>16,packed&65535;faces=struct.unpack_from('>I',cpu,0x64)[0]&65535
        if faces not in (1,6):raise ValueError('Unsupported explicit Xbox texture dimension')
        tiled=bool(code&256);endian=code>>6&3;swizzle=code>>18&4095
        pitch=((width+31)&~31) if tiled else (((width*FORMATS.get(fmt,1)+255)&~255)//FORMATS.get(fmt,1))
    else:
        if a&3!=2 or kind not in (1,3) or b&1024:raise ValueError('Unsupported Xbox texture dimension/stack')
        width,height=(size&8191)+1,(size>>13&8191)+1;faces=6 if kind==3 else 1;pitch=(a>>22&511)*32;tiled=bool(a>>31);endian=b>>6&3;swizzle=filtering>>1&4095
        if kind==3 and (size>>26)!=5:raise ValueError('Invalid Xbox cube face count')
    if fmt not in FORMATS or not 0<width<=8192 or not 0<height<=8192 or pitch<width or faces==6 and width!=height:raise ValueError('Unsupported uncompressed Xbox texture format/dimensions')
    source=cpu if gpu is None else gpu;start=(0x6c+struct.unpack_from('>i',cpu,0x6c)[0]-1) if gpu is None else struct.unpack_from('>I',cpu,0x6c)[0]-1
    length=struct.unpack_from('>I',cpu,0x70)[0]
    if fallback and not length:length=len(source)-start
    if start<0 or start+length>len(source):raise ValueError('Xbox raw texture exceeds component')
    bpp=FORMATS[fmt];stride=((pitch*((height+31)&~31)*bpp+4095)&~4095) if faces==6 else 0
    packed=not fallback and bool(dimension&2048) and (min(width,height)-1).bit_length()<=4
    packed_x=16 if packed and (width-1).bit_length()<=(height-1).bit_length() else 0;packed_y=16 if packed and not packed_x else 0
    info=dict(format=fmt,width=width,height=height,faces=faces,pitch=pitch,tiled=tiled,endian=endian,swizzle=swizzle,start=start,length=length,bpp=bpp,face_stride=stride,packed_x=packed_x,packed_y=packed_y,runtime_generated=fallback)
    return info


def addresses(info,face=None):
    faces=range(info['faces']) if face is None else (face,);swap=(0,1,3,2)[info['endian']];bpp=info['bpp']
    for f in faces:
        if not 0<=f<info['faces']:raise ValueError('Invalid cube face')
        for y in range(info['height']):
            for x in range(info['width']):
                px,py=x+info.get('packed_x',0),y+info.get('packed_y',0);off=f*info['face_stride']+(tiled_offset(px,py,info['pitch'],bpp.bit_length()-1) if info['tiled'] else (py*info['pitch']+px)*bpp)
                for j in range(bpp):
                    address=(off+j)^swap
                    if address<0 or address>=info['length']:raise ValueError('Xbox raw texel address exceeds component extent')
                    yield address


def linear(cpu,gpu=None):
    info=describe(cpu,gpu);source=cpu if gpu is None else gpu
    return info,bytes(source[info['start']+offset] for offset in addresses(info))


def export_dds(cpu,gpu=None):
    info,payload=linear(cpu,gpu);fmt=info['format'];header=bytearray(128);header[:4]=b'DDS ';struct.pack_into('<7I',header,4,124,0x100f,info['height'],info['width'],info['width']*info['bpp'],0,1);header[32:36]=b'XRAW';struct.pack_into('<II',header,36,fmt,info['swizzle']);struct.pack_into('<I',header,76,32);extra=b''
    if fmt in DXGI:struct.pack_into('<I4s',header,80,4,b'DX10');extra=struct.pack('<5I',DXGI[fmt],3,4 if info['faces']==6 else 0,1,0)
    elif fmt==2:struct.pack_into('<7I',header,80,0x20000,0,8,255,0,0,0)
    elif fmt==4:
        swizzle=[info['swizzle']>>(i*3)&7 for i in range(3)];masks=[31,2016,63488];rgb=[masks[i] for i in swizzle] if set(swizzle)=={0,1,2} else masks
        struct.pack_into('<7I',header,80,0x40,0,16,*rgb,0)
    else:
        swizzle=[info['swizzle']>>(i*3)&7 for i in range(4)];masks=[255,65280,16711680,4278190080];rgba=[masks[i] for i in swizzle] if set(swizzle)=={0,1,2,3} else masks
        struct.pack_into('<7I',header,80,0x41,0,32,*rgba)
    struct.pack_into('<II',header,108,0x1008 if info['faces']==6 else 0x1000,0xfe00 if info['faces']==6 else 0)
    return bytes(header)+extra+payload


def dds_info(data):
    if len(data)<128 or data[:4]!=b'DDS ' or struct.unpack_from('<I',data,4)[0]!=124:raise ValueError('Invalid raw DDS header')
    h,w=struct.unpack_from('<II',data,12);mips=max(1,struct.unpack_from('<I',data,28)[0]);flags,code,bits=struct.unpack_from('<3I',data,80);offset=128;faces=6 if struct.unpack_from('<I',data,112)[0]&0x200 else 1
    if struct.unpack_from('<I',data,76)[0]!=32 or struct.unpack_from('<I',data,24)[0]>1 or struct.unpack_from('<I',data,112)[0] not in (0,0xfe00):raise ValueError('Unsupported raw DDS depth/cube caps')
    if code==0x30315844:
        if len(data)<148:raise ValueError('Truncated raw DX10 DDS')
        dxgi,dimension,misc,array,alpha=struct.unpack_from('<5I',data,128);fmt=next((fmt for fmt,value in DXGI.items() if value==dxgi),None);offset=148
        if dimension!=3 or array!=1 or bool(misc&4)!=(faces==6):raise ValueError('Unsupported raw DDS dimension/array')
    elif flags==0x20000 and bits==8:fmt=2
    elif flags==0x40 and bits==16:fmt=4
    elif flags==0x41 and bits==32:fmt=6
    else:raise ValueError('Unsupported uncompressed DDS pixel format')
    if fmt not in FORMATS or not 0<w<=8192 or not 0<h<=8192 or mips!=1 or len(data)!=offset+w*h*FORMATS[fmt]*faces:raise ValueError('Raw DDS dimensions/base payload do not match')
    if data[32:36]==b'XRAW':
        stored,swizzle=struct.unpack_from('<II',data,36)
        if stored!=fmt:raise ValueError('Raw DDS format marker mismatch')
    else:swizzle=0x688
    return dict(width=w,height=h,mips=1,fourcc='RAW'+str(fmt),raw_format=fmt,faces=faces,data_offset=offset,swizzle=swizzle)


def channels(pixel,fmt):
    if fmt==2:return [pixel[0]]*4
    if fmt==4:
        word=int.from_bytes(pixel,'little');return [round((word&31)*255/31),round((word>>5&63)*255/63),round((word>>11&31)*255/31),255]
    if fmt==6:return list(pixel)
    if fmt==10:return [pixel[0],pixel[1],pixel[1],pixel[1]]
    values=struct.unpack('<'+('2e' if fmt==31 else '4e'),pixel);converted=[round(max(0.,min(1.,v))*255) if math.isfinite(v) else 0 for v in values]
    return converted+[converted[-1]]*(4-len(converted))


def image_from_dds(data,face=0):
    info=dds_info(data);fmt=info['raw_format'];bpp=FORMATS[fmt];size=info['width']*info['height']*bpp
    if not 0<=face<info['faces']:raise ValueError('Invalid cube face')
    payload=data[info['data_offset']+face*size:info['data_offset']+(face+1)*size];rgba=bytearray();swizzle=[info['swizzle']>>(i*3)&7 for i in range(4)]
    if any(i>5 for i in swizzle):raise ValueError('Unsupported Xbox component swizzle')
    for off in range(0,len(payload),bpp):
        values=channels(payload[off:off+bpp],fmt)+[0,255];rgba.extend(values[i] for i in swizzle)
    return Image.frombytes('RGBA',(info['width'],info['height']),bytes(rgba))


def save_dds(resource,payload):
    blocks=resource.blocks();cpu=blocks[0];gpu=blocks[1] if len(blocks)>1 else None;info=describe(cpu,gpu);incoming=dds_info(payload)
    if (incoming['width'],incoming['height'],incoming['raw_format'],incoming['faces'])!=(info['width'],info['height'],info['format'],info['faces']):raise ValueError('Raw DDS must retain Xbox dimensions, format and face count')
    source=cpu if gpu is None else gpu;data=bytearray(source);pixels=payload[incoming['data_offset']:]
    original=export_dds(cpu,gpu)
    if payload[76:108]!=original[76:108]:raise ValueError('Raw DDS pixel masks/encoding must match the exported source')
    for offset,value in zip(addresses(info),pixels):data[info['start']+offset]=value
    if hasattr(resource,'workspace'):resource.workspace.require('direct_resources')
    target=resource.component_path(0 if gpu is None else 1);atomic_write(target,bytes(data),sha(source));return target


def save_bc_base(resource,payload):
    from . import dds
    blocks=resource.blocks();cpu=blocks[0];gpu=blocks[1] if len(blocks)>1 else None;original=dds.xbox_dds(cpu,gpu);info=dds.info(original);incoming=dds.info(payload)
    if (incoming['width'],incoming['height'],incoming['fourcc'],incoming['mips'])!=(info['width'],info['height'],info['fourcc'],1):raise ValueError('Packed BC edits retain native base dimensions and format')
    a,b,size,_,lod,dim=struct.unpack_from('>6I',cpu,0x94);bpp=dds.FORMATS[b&63][1];width,height=info['width'],info['height'];pitch=(a>>22&511)*8;px=4 if (width-1).bit_length()<=(height-1).bit_length() else 0;py=4 if not px else 0;source=cpu if gpu is None else gpu;start=0x6c+struct.unpack_from('>i',cpu,0x6c)[0]-1 if gpu is None else struct.unpack_from('>I',cpu,0x6c)[0]-1;length=struct.unpack_from('>I',cpu,0x70)[0];data=bytearray(source);swap=(0,1,3,2)[b>>6&3];cursor=128
    for y in range((height+3)//4):
        for x in range((width+3)//4):
            off=tiled_offset(x+px,y+py,pitch,bpp.bit_length()-1) if a>>31 else ((y+py)*pitch+x+px)*bpp
            if off+bpp>length:raise ValueError('Packed BC block exceeds source extent')
            for j in range(bpp):data[start+off+(j^swap)]=payload[cursor+j]
            cursor+=bpp
    if hasattr(resource,'workspace'):resource.workspace.require('direct_resources')
    target=resource.component_path(0 if gpu is None else 1);atomic_write(target,bytes(data),sha(source));return target


def from_image(path,baseline,face=0):
    info=dds_info(baseline);fmt=info['raw_format'];width,height=info['width'],info['height'];bpp=FORMATS[fmt]
    with Image.open(path) as source:
        if source.size!=(width,height):raise ValueError('Uncompressed image edits retain native dimensions; native upscaling currently uses BC1-BC5 DDS')
        incoming=source.convert('RGBA').tobytes()
    before=image_from_dds(baseline,face).tobytes();size=width*height*bpp;start=info['data_offset']+face*size;result=bytearray(baseline);swizzle=[info['swizzle']>>(j*3)&7 for j in range(4)];count={2:1,4:3,6:4,10:2,31:2,32:4}[fmt]
    for i in range(width*height):
        rgba=incoming[i*4:i*4+4]
        if rgba==before[i*4:i*4+4]:continue
        offset=start+i*bpp;old=bytes(result[offset:offset+bpp]);old_channels=channels(old,fmt);wanted={}
        for j,s in enumerate(swizzle):
            if fmt==4 and s==3:
                if rgba[j]!=255:raise ValueError('RGB565 has no editable alpha channel')
                continue
            if s>=4:
                if rgba[j]!=(0 if s==4 else 255):raise ValueError('Image changes a constant Xbox channel')
                continue
            channel=min(s,count-1)
            if channel in wanted and wanted[channel]!=rgba[j]:raise ValueError('Image colors cannot be represented by this Xbox channel layout')
            wanted[channel]=rgba[j]
        if fmt in (2,6,10):
            pixel=bytearray(old)
            for channel,value in wanted.items():pixel[channel]=value
        elif fmt==4:
            word=int.from_bytes(old,'little')
            for channel,value in wanted.items():
                shift,bits=((0,5),(5,6),(11,5))[channel];mask=((1<<bits)-1)<<shift;word=(word&~mask)|(round(value*((1<<bits)-1)/255)<<shift)
            pixel=word.to_bytes(2,'little')
        else:
            pixel=bytearray(old)
            for channel,value in wanted.items():
                if value!=old_channels[channel]:struct.pack_into('<e',pixel,channel*2,value/255)
        result[offset:offset+bpp]=pixel
    return bytes(result)
