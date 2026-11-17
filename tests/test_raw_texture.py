import struct
from types import SimpleNamespace
import pytest
from choops_recomp import raw_texture as raw,dds


def fixture(tmp_path,fmt,tiled,endian,faces=1):
    bpp=raw.FORMATS[fmt];stride=(32*32*bpp+4095)&~4095;gpu=bytes(i%251 for i in range(stride*faces+256));cpu=bytearray(224);struct.pack_into('>II',cpu,0x6c,1,stride*faces);struct.pack_into('>6I',cpu,0x94,2|(1<<22)|(int(tiled)<<31),fmt|(endian<<6),31|(31<<13)|((5 if faces==6 else 0)<<26),0x688<<1,0,(3 if faces==6 else 1)<<9)
    path=tmp_path/'gpu.dat';path.write_bytes(gpu);resource=SimpleNamespace(blocks=lambda:[bytes(cpu),path.read_bytes()],component_path=lambda index:path)
    return resource,bytes(cpu),gpu,path


@pytest.mark.parametrize('fmt',list(raw.FORMATS))
@pytest.mark.parametrize('tiled,endian',[(False,0),(True,1),(True,2)])
def test_raw_dds_roundtrip_and_single_byte_edit_preserve_unclaimed_data(tmp_path,fmt,tiled,endian):
    resource,cpu,gpu,path=fixture(tmp_path,fmt,tiled,endian);payload=dds.xbox_dds(cpu,gpu);assert dds.image(payload).size==(32,32);raw.save_dds(resource,payload);assert path.read_bytes()==gpu
    value=bytearray(payload);value[raw.dds_info(payload)['data_offset']]^=1;raw.save_dds(resource,value);changed=path.read_bytes()
    assert sum(a!=b for a,b in zip(gpu,changed))==1 and changed[-256:]==gpu[-256:]


@pytest.mark.parametrize('fmt',[31,32])
def test_half_float_cube_preserves_other_faces(tmp_path,fmt):
    resource,cpu,gpu,path=fixture(tmp_path,fmt,True,1,6);payload=bytearray(raw.export_dds(cpu,gpu));info=raw.dds_info(payload);assert info['faces']==6
    payload[info['data_offset']+5*32*32*raw.FORMATS[fmt]]^=1;raw.save_dds(resource,payload);assert sum(a!=b for a,b in zip(gpu,path.read_bytes()))==1


def test_image_export_import_keeps_half_float_precision_when_unchanged(tmp_path):
    resource,cpu,gpu,path=fixture(tmp_path,32,True,1);payload=raw.export_dds(cpu,gpu);image=raw.image_from_dds(payload);png=tmp_path/'art.png';image.save(png)
    assert raw.from_image(png,payload)==payload


def test_explicit_runtime_descriptor_fallback_uses_linear_pitch_and_argb_swizzle(tmp_path):
    resource,cpu,gpu,path=fixture(tmp_path,6,False,2);cpu=bytearray(cpu);struct.pack_into('>I',cpu,8,0x18280086);struct.pack_into('>I',cpu,0x60,(32<<16)|32);struct.pack_into('>I',cpu,0x64,0x10001);struct.pack_into('>I',cpu,0x70,0);struct.pack_into('>6I',cpu,0x94,2,0,0,0,0,0);gpu=bytes(8192)
    info=raw.describe(cpu,gpu);assert info['format']==6 and info['pitch']==64 and info['swizzle']==0x60a
