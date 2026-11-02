import io
import struct
import wave
from types import SimpleNamespace
import pytest
from choops_recomp import audio,scene,uniforms
from choops_recomp.binary import Binary
from choops_recomp.roster import Roster,TABLES
from choops_recomp.player_fields import FIELDS
from choops_recomp.workspace import atomic_write,sha


def roster_bytes():
    data=bytearray(256)
    for table,(field,bias,stride,_) in TABLES.items():
        start=len(data);data.extend(bytes(stride+64))
        struct.pack_into('>I',data,field,1)
        struct.pack_into('>i',data,field+4,start-(field+4)+bias)
    model=Roster(data)
    off=model.rows['uniforms'][0]['offset']
    struct.pack_into('>II',data,off,(2<<22)|(6<<12)|0x800,0xE0123456)
    return bytes(data)


def test_uniform_append_preserves_original_table_and_unknown_bits():
    original=roster_bytes();model=Roster(original);old=uniforms.rows(model)[0]
    new=Roster(uniforms.append(model,0,2,900,2));rows=uniforms.rows(new)
    assert rows[0]==old
    assert (rows[1]['owner'],rows[1]['asset'],rows[1]['variant'])==(2,900,2)
    assert rows[1]['word1']==old['word1']
    assert rows[1]['word0']&0x800==old['word0']&0x800
    assert bytes(new.data[0x78:len(original)])==original[0x78:]
    assert bytes(model.data)==original


def test_uniform_rejects_duplicate_owner_variant():
    model=Roster(roster_bytes())
    with pytest.raises(ValueError,match='already'):uniforms.append(model,0,2,900,0)


def test_roster_undo_redo_and_growth_preserve_other_fields():
    model=Roster(roster_bytes());original=bytes(model.data)
    model.set_string('players',0,'last_name','Longer Xbox Name')
    assert model.rows['players'][0]['last_name']=='Longer Xbox Name'
    edited=bytes(model.data);model.undo();assert bytes(model.data)==original
    model.redo();assert bytes(model.data)==edited
    model.set_rating(0,2,81.6)
    assert model.rows['players'][0]['ratings'][2]==81.6


def test_atomic_write_rejects_external_changes(tmp_path):
    p=tmp_path/'asset';p.write_bytes(b'old');expected=sha(p.read_bytes());p.write_bytes(b'external')
    with pytest.raises(ValueError,match='changed'):atomic_write(p,b'edit',expected)
    assert p.read_bytes()==b'external'


def test_pcm_import_rejects_truncation_and_canonicalizes(tmp_path):
    header=struct.pack('>11I',1,5,2,4,16000,0,2048,0,0,0,0)
    resource=SimpleNamespace(blocks=lambda:[header,bytes(2048)],folder=tmp_path/'audio',record={'index':7})
    source=tmp_path/'input.wav'
    with wave.open(str(source),'wb') as f:
        f.setparams((1,2,16000,0,'NONE',''));f.writeframes(b'\x01\x00'*4)
    marker=audio.import_wav(resource,source)
    assert marker['samples']==4
    assert (resource.folder/'audio.wav').read_bytes()[20:22]==b'\x01\x00'
    source.write_bytes(source.read_bytes()[:-2])
    with pytest.raises(ValueError,match='Truncated'):audio.import_wav(resource,source)


def test_scene_transform_preserves_uv_rgba():
    matrix=(1,0,0,0,0,1,0,0,0,0,1,0,10,20,30,1)
    vertices=[(1,2,3,.5,.25,1,0,0,1)]
    assert scene.transform(vertices,matrix)==[(11,22,33,.5,.25,1,0,0,1)]


def test_instance_table_rejects_nonhomogeneous_matrix():
    data=bytearray(256);struct.pack_into('>II',data,0x3c,1,0x80-0x40+1)
    with pytest.raises(ValueError,match='instance'):scene.instances(Binary(data))


@pytest.mark.parametrize('field',list(FIELDS))
def test_player_property_keeps_all_other_properties(field):
    model=Roster(roster_bytes());before=dict(model.rows['players'][0]);spec=FIELDS[field]
    model.set_player(0,field,spec['maximum'])
    after=model.rows['players'][0]
    assert after[field]==spec['maximum']
    for other in FIELDS:
        if other!=field:assert after[other]==before[other]
    model.undo();assert model.data==bytearray(roster_bytes())


def test_xbox_weight_and_handedness_use_native_masks():
    model=Roster(roster_bytes());off=model.rows['players'][0]['offset']
    model.set_player(0,'weight_lbs',180);model.set_player(0,'hand_code',1)
    assert struct.unpack_from('>I',model.data,off+0x9c)[0]==180<<5
    assert struct.unpack_from('>I',model.data,off+0x94)[0]==1<<14


def test_xbox_jukebox_categories_and_indices():
    from choops_recomp.audio_catalog import tracks,LICENSED,BAND
    catalog=tracks()
    assert set(catalog)==set(range(87))
    assert sum(r['category']==LICENSED for r in catalog.values())==23
    assert sum(r['category']==BAND for r in catalog.values())==64
    assert catalog[10]['title']=='Hi Hi Yikas'
    assert catalog[11]['title']=='Yea Alabama'
    assert catalog[74]['title']=="You're Doing It"


def test_transaction_rolls_back_invalid_late_change():
    model=Roster(roster_bytes());before=bytes(model.data)
    with pytest.raises(ValueError):
        with model.transaction():
            model.set_player(0,'weight_lbs',180)
            model.set_player(0,'hand_code',9)
    assert bytes(model.data)==before and not model.history


def test_csv_selective_review_and_single_undo(tmp_path):
    import csv
    from choops_recomp import roster_csv
    model=Roster(roster_bytes());source=tmp_path/'players.csv';roster_csv.export(model,'players',source)
    with source.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);columns=reader.fieldnames;rows=list(reader)
    rows[0]['first_name']='Xbox Name';rows[0]['weight_lbs']='180'
    with source.open('w',encoding='utf-8-sig',newline='') as f:writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    changes=roster_csv.review(model,source);assert len(changes)==2
    assert model.rows['players'][0]['first_name']==''
    roster_csv.apply(model,changes,{'first_name'})
    assert model.rows['players'][0]['first_name']=='Xbox Name'
    assert model.rows['players'][0]['weight_lbs']==0
    assert len(model.history)==1
    model.undo();assert model.data==bytearray(roster_bytes())
