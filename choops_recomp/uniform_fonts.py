"""Xbox indexed uniform artwork and bounded authored glyph composition.

Xbox fonts have an uninitialized GPU fetch: decode their explicit dimensions
and one-based palette pointer, not a guessed generic texture format.
"""
import math,struct
from pathlib import Path
from PIL import Image
from .workspace import atomic_write,sha


def pixels(image):
    return image.get_flattened_data() if hasattr(image,'get_flattened_data') else image.getdata()


def resource(workspace,filename,name,kind):
    import zlib
    identity=zlib.crc32(name.encode('ascii'))&0xffffffff;bank=zlib.crc32(filename.upper().encode('ascii'))&0xffffffff
    matches=[r for r in workspace.resources if r.entry['hash']==bank and r.record['id']==identity and r.record['type']==kind]
    if len(matches)!=1:raise ValueError('Missing or ambiguous Xbox uniform resource: '+filename+'/'+name)
    return matches[0]


def layout(blocks):
    if len(blocks)!=2 or len(blocks[0])!=224:raise ValueError('Unsupported Xbox indexed uniform atlas')
    cpu,gpu=blocks
    if struct.unpack_from('>I',cpu,8)[0]!=0x24820002 or struct.unpack_from('>I',cpu,0x6c)[0]!=1:raise ValueError('Unsupported Xbox font descriptor')
    dimension=struct.unpack_from('>I',cpu,0x60)[0];width,height=dimension>>16,dimension&65535;palette=struct.unpack_from('>I',cpu,0x68)[0]-1
    if not all(0<v<=8192 and not v&(v-1) for v in (width,height)) or palette+1024!=len(gpu):raise ValueError('Invalid Xbox indexed dimensions/palette')
    levels=[];offset=0;w,h=width,height
    while True:
        levels.append((offset,w,h));offset+=w*h
        if (w,h)==(1,1):break
        w,h=max(1,w//2),max(1,h//2)
    if (offset+15)&~15!=palette:raise ValueError('Xbox font mip extent does not match palette pointer')
    return width,height,palette,levels


def atlas(blocks):
    width,height,palette,levels=layout(blocks);gpu=blocks[1];colors=[bytes((r,g,b,a)) for a,r,g,b in struct.iter_unpack('4B',gpu[palette:palette+1024])]
    return Image.frombytes('RGBA',(width,height),b''.join(colors[i] for i in gpu[:width*height]))


def save_atlas(target,path):
    blocks=target.blocks();width,height,palette,levels=layout(blocks)
    with Image.open(path) as opened:
        if opened.size!=(width,height):raise ValueError('Indexed font artwork must retain its Xbox dimensions')
        incoming=opened.convert('RGBA')
    if incoming.tobytes()==atlas(blocks).tobytes():return False
    colors=incoming.getcolors(256)
    if colors is None:raise ValueError('Xbox indexed font artwork supports at most 256 exact RGBA colors; reduce its palette before import')
    values=sorted(color for count,color in colors);lookup={color:i for i,color in enumerate(values)};indices=Image.frombytes('P',(width,height),bytes(lookup[p] for p in pixels(incoming)));gpu=bytearray(blocks[1])
    for offset,w,h in levels:gpu[offset:offset+w*h]=indices.resize((w,h),Image.Resampling.NEAREST).tobytes()
    # Retain source alignment padding; all mip indices use this one ARGB table.
    table=values+[(0,0,0,0)]*(256-len(values));gpu[palette:palette+1024]=bytes(c for r,g,b,a in table for c in (a,r,g,b))
    atlas([blocks[0],bytes(gpu)]);atomic_write(target.component_path(1),bytes(gpu),sha(blocks[1]));return True


def metrics(blocks,width,count):
    if len(blocks)!=1 or len(blocks[0])<count*4:raise ValueError('Truncated Xbox glyph metrics')
    values=list(struct.iter_unpack('>2H',blocks[0][:count*4]))
    if any(not size or x+((size+3)&~3)>width for x,size in values):raise ValueError('Xbox glyph metric exceeds atlas')
    return values


def save_metrics(target,atlas_resource,values):
    width,height,palette,levels=layout(atlas_resource.blocks());blocks=target.blocks();count=len(values)
    if count not in (10,28):raise ValueError('Expected ten number or 28 surname glyphs')
    original=metrics(blocks,width,count);data=bytearray(blocks[0])
    for i,pair in enumerate(values):
        if len(pair)!=2 or any(type(v) is not int or not 0<=v<=65535 for v in pair):raise ValueError('Invalid glyph metric')
        struct.pack_into('>2H',data,i*4,*pair)
    metrics([data],width,count);atomic_write(target.component_path(),bytes(data),sha(blocks[0]));return count


def glyphs(workspace,filename,role):
    name='jersey_numbers' if role=='numbers' else 'names';image=atlas(resource(workspace,filename,name,0x5c369069).blocks());values=metrics(resource(workspace,filename,role,0x68b693b2).blocks(),image.width,10 if role=='numbers' else 28)
    return image,values


def number_image(image,values,number,size):
    if type(number) is not int or not 0<=number<=100:raise ValueError('Choose jersey number 0-99, or 100 for 00')
    digits=[0,0] if number==100 else [number//10,number%10] if number>=10 else [number];out=Image.new('RGBA',size);left=(size[0]-sum(values[d][1] for d in digits))//2
    for digit in digits:
        x,width=values[digit];copy=(width+3)&~3
        if left<0 or left+copy>size[0] or image.height>size[1]:raise ValueError('Number artwork exceeds template')
        out.paste(image.crop((x,0,x+copy,image.height)),(left,0));left+=(width+5)&~3
    return out


def name_image(image,values,text,size):
    indices=[]
    for c in text:
        if c=="'":indices.append(0)
        elif c in '- ':indices.append(1)
        elif 'A'<=c.upper()<='Z' and len(c.upper())==1:indices.append(ord(c.upper())-65+2)
        else:raise ValueError('Unsupported Xbox surname glyph: '+c)
    if not 1<=len(indices)<=64:raise ValueError('Enter 1-64 surname characters')
    extent=lambda spacing:sum((values[i][1]+spacing+3)&~3 for i in indices)-spacing
    spacing=max(1,25-extent(0)//len(indices))
    if extent(spacing)>size[0]-10 and len(indices)>2:
        spacing=25
        for _ in range(3):
            total=extent(spacing)
            if total<=size[0]-10:break
            spacing-=(total-(size[0]-10)+len(indices)-2)//(len(indices)-2)
    left=int((size[0]-extent(spacing))/2);out=Image.new('RGBA',size)
    for c,index in zip(text,indices):
        x,width=values[index];copy=(width+3)&~3
        if left<0 or left+copy>size[0] or image.height>size[1]:raise ValueError('Surname artwork exceeds template')
        if c!=' ':out.paste(image.crop((x,0,x+copy,image.height)),(left,0))
        left+=(width+spacing+3)&~3
    return out


def placement(workspace):
    data=resource(workspace,'global.iff','unidata',0x070d3d6b).blocks()[0]
    if len(data)!=96:raise ValueError('Unsupported Xbox uniform placement record')
    x,y,radius,angle,scale=struct.unpack_from('>5f',data,8)
    if not all(math.isfinite(v) for v in (x,y,radius,angle,scale)) or min(radius,angle,scale)<=0:raise ValueError('Invalid Xbox surname placement')
    transforms=[]
    for offset in (0x1c,0x2c):
        a,b,w,h=struct.unpack_from('>4f',data,offset)
        if not all(math.isfinite(v) for v in (a,b,w,h)) or min(w,h)<=0:raise ValueError('Invalid Xbox number placement')
        transforms.append((1/w,1/h,.5-a/w,.5-b/h))
    return transforms,(x,y,radius,angle),scale


def template(workspace,name):
    cpu=resource(workspace,'global.iff',name,0x5c369069).blocks()[0];dimension=struct.unpack_from('>I',cpu,0x60)[0];size=dimension>>16,dimension&65535
    if not all(0<v<=1024 for v in size):raise ValueError('Invalid Xbox glyph template size')
    return size
