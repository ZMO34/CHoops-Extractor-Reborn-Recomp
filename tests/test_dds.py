import struct
import pytest
from choops_recomp import dds
from choops_recomp.uniforms import _private_image


def texture(fmt):
    data=bytearray(0x3000);struct.pack_into('>iI',data,0x6c,0x1000-0x6c+1,0x2000)
    struct.pack_into('>6I',data,0x94,0x80400002,fmt|64,31|(31<<13),0,0,1<<9)
    # Constant endpoint-only BC blocks are independently re-encodable.
    block=bytes((0,255,0,0,0,0,0,0));data[0x1000:]=block*(0x2000//8)
    return bytes(data)


@pytest.mark.parametrize('fmt,code',[(18,'DXT1'),(19,'DXT3'),(20,'DXT5'),(49,'ATI2'),(59,'ATI1')])
def test_xbox_dds_formats_have_exact_payload_and_decode(fmt,code):
    exported=dds.xbox_dds(texture(fmt));info=dds.info(exported)
    assert info['fourcc']==code and (info['width'],info['height'])==(32,32)
    assert dds.image(exported).size==(32,32)
    with pytest.raises(ValueError,match='payload'):dds.info(exported[:-1])


@pytest.mark.parametrize('fmt',[49,59])
def test_private_bc_mask_encoding_changes_identity_without_changing_pixels(fmt):
    source=texture(fmt);private,original=_private_image(source,None,'uniform-test-'+str(fmt))
    edited=dds.xbox_dds(private)
    assert edited!=original
    assert dds.image(edited).tobytes()==dds.image(original).tobytes()


@pytest.mark.parametrize('fmt',[18,19,20,49,59])
def test_image_import_retains_upscale_and_creates_complete_mips(tmp_path,fmt):
    from PIL import Image
    source=tmp_path/'art.png';Image.new('RGBA',(64,64),(64,64,64,255)).save(source)
    baseline=dds.xbox_dds(texture(fmt));encoded=dds.from_image(source,baseline)
    assert dds.info(encoded)==dict(width=64,height=64,mips=7,fourcc=dds.FORMATS[fmt][0].decode())
    assert dds.image(encoded).size==(64,64)
    if fmt==59:assert dds.image(encoded).getpixel((0,0))==(64,64,64,255)


def test_image_import_does_not_downsize_or_distort_artwork(tmp_path):
    from PIL import Image
    source=tmp_path/'art.png';Image.new('RGB',(16,16)).save(source)
    with pytest.raises(ValueError,match='aspect'):dds.from_image(source,dds.xbox_dds(texture(18)))
