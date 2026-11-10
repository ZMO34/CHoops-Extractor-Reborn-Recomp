import struct
from types import SimpleNamespace
import pytest
from PIL import Image
from choops_recomp import uniforms,uniform_fonts as fonts
from test_relationships import roster


def model():
    m=roster();start=m.tables['uniforms'][0]
    for i,(owner,variant) in enumerate(((0,0),(0,1),(1,0),(1,1))):struct.pack_into('>II',m.data,start+i*8,(owner<<22)|(10<<12)|(variant<<8)|0x800,0xa1234567)
    for i in range(2):struct.pack_into('>H',m.data,m.rows['teams'][i]['offset']+0x190,0)
    m.reload();return m


def test_checked_uniform_edit_preserves_unknown_bits(monkeypatch):
    m=model();before=bytes(m.data);monkeypatch.setattr(uniforms,'validate_asset',lambda *args:None);uniforms.edit(m,None,0,asset=900,shape=4,unlock=0)
    row=uniforms.rows(m)[0];assert (row['asset'],row['shape'],row['unlock'])==(900,4,0)
    assert row['word0']&0x800 and row['word1']&~(7<<27)==0xa1234567&~(7<<27)
    m.undo();assert bytes(m.data)==before
    with pytest.raises(ValueError,match='already'):uniforms.edit(m,None,0,variant=1)


def test_private_owner_preserves_shared_school_routing():
    m=model();before=bytes(m.data);old=uniforms.rows(m);new=uniforms.detach(m,0)
    assert uniforms.owner(m,0)==new and uniforms.owner(m,1)==0 and new not in (0,1)
    current=uniforms.rows(m);assert current[:4]==old
    assert [r['asset'] for r in current if r['owner']==new]==[10,10]
    assert len(m.history)==1;m.undo();assert bytes(m.data)==before


def test_uniform_missing_artwork_rejects_without_mutation():
    m=model();before=bytes(m.data)
    with pytest.raises(ValueError,match='Missing Xbox'):uniforms.edit(m,SimpleNamespace(by_hash={}),0,asset=900)
    assert bytes(m.data)==before


def test_alternate_availability_preserves_complete_rows_and_survives_growth(monkeypatch):
    m=model();monkeypatch.setattr(uniforms,'validate_asset',lambda *args:None)
    m._commit(uniforms.append(m,0,0,900,2));before=bytes(m.data);original=uniforms.rows(m)[-1]
    uniforms.set_available(m,None,0,2,False)
    assert not any(r['owner']==0 and r['variant']==2 for r in uniforms.rows(m))
    dormant=uniforms.disabled(m);assert len(dormant)==1 and dormant[0]['word0']==original['word0'] and dormant[0]['word1']==original['word1']
    with pytest.raises(ValueError,match='disabled'):uniforms.append(m,0,0,901,2)
    m.set_string('players',0,'last_name','Appended after dormant metadata')
    uniforms.set_available(m,None,0,2,True)
    assert not uniforms.disabled(m);assert uniform_values(uniforms.rows(m)[-1])==uniform_values(original)


def uniform_values(row):return row['word0'],row['word1']


def test_disabled_state_is_undoable_and_corruption_is_rejected(monkeypatch):
    m=model();m._commit(uniforms.append(m,0,0,900,2));before=bytes(m.data)
    uniforms.set_available(m,None,0,2,False);m.undo();assert bytes(m.data)==before
    uniforms.set_available(m,None,0,2,False);m.data[-1]^=1
    with pytest.raises(ValueError,match='dormant'):uniforms.disabled(m)


def atlas(tmp_path):
    cpu=bytearray(224);struct.pack_into('>I',cpu,8,0x24820002);struct.pack_into('>I',cpu,0x60,(1024<<16)|32);struct.pack_into('>II',cpu,0x68,43713,1)
    gpu=bytearray(44736);gpu[43711]=0x7e;gpu[43712:43720]=bytes((0,0,0,0,255,255,255,255));gpu[:1024*32]=bytes([0,1])*16384
    path=tmp_path/'atlas.dat';path.write_bytes(gpu)
    resource=SimpleNamespace(blocks=lambda:[bytes(cpu),path.read_bytes()],component_path=lambda index:path)
    return resource,path,bytes(cpu),bytes(gpu)


def test_xbox_font_roundtrip_and_replacement_preserve_descriptor_and_padding(tmp_path):
    r,path,cpu,gpu=atlas(tmp_path);image=fonts.atlas(r.blocks());assert image.size==(1024,32);png=tmp_path/'art.png';image.save(png)
    assert fonts.save_atlas(r,png) is False and path.read_bytes()==gpu
    image.putpixel((0,0),(200,0,0,255));image.save(png);assert fonts.save_atlas(r,png)
    assert fonts.atlas(r.blocks()).tobytes()==image.tobytes();assert r.blocks()[0]==cpu;assert path.read_bytes()[43711]==0x7e


def test_xbox_font_rejects_lossy_or_resized_import(tmp_path):
    r,path,cpu,gpu=atlas(tmp_path);png=tmp_path/'art.png';image=Image.new('RGBA',(1024,32));image.putdata([(i%256,(i//256)%256,0,255) for i in range(1024*32)]);image.save(png)
    with pytest.raises(ValueError,match='256 exact'):fonts.save_atlas(r,png)
    Image.new('RGBA',(512,32)).save(png)
    with pytest.raises(ValueError,match='dimensions'):fonts.save_atlas(r,png)
    assert path.read_bytes()==gpu


def test_wide_xbox_surname_atlas_and_metrics():
    cpu=bytearray(224);struct.pack_into('>I',cpu,8,0x24820002);struct.pack_into('>I',cpu,0x60,(2048<<16)|32);struct.pack_into('>II',cpu,0x68,87425,1)
    gpu=bytes(88448);assert fonts.atlas([cpu,gpu]).size==(2048,32)
    values=struct.pack('>2H',1500,40)*28;assert fonts.metrics([values],2048,28)==[(1500,40)]*28


def test_font_metric_edit_preserves_trailing_words_and_rejects_bounds(tmp_path):
    art,path,cpu,gpu=atlas(tmp_path);target=tmp_path/'metrics.dat';original=struct.pack('>2H',32,20)*10+b'UNKNOWN!';target.write_bytes(original)
    resource=SimpleNamespace(blocks=lambda:[target.read_bytes()],component_path=lambda:target);values=[(32,20)]*10;values[2]=(64,24)
    assert fonts.save_metrics(resource,art,values)==10;changed=target.read_bytes();assert changed[:8]==original[:8] and changed[12:]==original[12:]
    values[2]=(1020,20)
    with pytest.raises(ValueError,match='exceeds'):fonts.save_metrics(resource,art,values)
    assert target.read_bytes()==changed


def test_authored_glyph_composition_handles_double_zero_and_surnames():
    image=Image.new('RGBA',(1024,32));image.paste((255,0,0,255),(32,0,36,32));values=[(32,4)]*28
    zero=fonts.number_image(image,values,0,(64,32));double=fonts.number_image(image,values,100,(64,32));assert double.getbbox()[2]-double.getbbox()[0]>zero.getbbox()[2]-zero.getbbox()[0]
    assert fonts.name_image(image,values,"O'NEIL",(256,32)).getbbox()
    with pytest.raises(ValueError):fonts.number_image(image,values,101,(64,32))
    with pytest.raises(ValueError):fonts.name_image(image,values,'\u2603',(256,32))
