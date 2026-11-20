"""Bounded read-only inspection of a selected resource's owning files."""
def components(resource):
    result=[]
    for index,c in enumerate(resource.components):
        if 'file' in c:
            path=resource.workspace.safe(c['file']);offset=c['offset'];size=c['size'];encoding='source component (may be compressed)'
        else:
            relative=c.get('folder',resource.entry['folder'])
            if c.get('path') is None:
                result.append(dict(index=index,path=None,offset=0,size=0,encoding='empty'));continue
            path=resource.workspace.safe(relative+'/'+c['path']);offset=0;size=path.stat().st_size;encoding='loose component'
        if offset<0 or size<0 or offset+size>path.stat().st_size:raise ValueError('Resource extent exceeds its owning file')
        result.append(dict(index=index,path=path,offset=offset,size=size,encoding=encoding))
    return result


def page(resource,component=0,offset=0,length=4096):
    if not 0<=length<=65536 or offset<0:raise ValueError('Inspection pages are limited to 64 KiB')
    entries=components(resource)
    if not 0<=component<len(entries):raise ValueError('Unknown resource component')
    entry=entries[component]
    if offset>entry['size']:raise ValueError('Inspection offset exceeds resource component')
    size=min(length,entry['size']-offset)
    if entry['path'] is None:return b''
    with entry['path'].open('rb') as stream:stream.seek(entry['offset']+offset);data=stream.read(size)
    if len(data)!=size:raise ValueError('Resource changed while inspecting')
    return data


def hex_text(data,offset=0):
    rows=[]
    for i in range(0,len(data),16):
        block=data[i:i+16];text=''.join(chr(b) if 32<=b<127 else '.' for b in block)
        rows.append(f'{offset+i:08x}  {block.hex(" "):<47}  {text}')
    return '\n'.join(rows)
