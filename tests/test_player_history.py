import struct
import pytest
from choops_recomp import conference_history,roster_csv
from choops_recomp.footwear import texture
from choops_recomp.ui.app import PlayerDetailsModel
from test_relationships import roster


def test_native_redshirt_side_effects_are_one_undoable_edit():
    m=roster();m.set_player(0,'redshirt_code',2);before=bytes(m.data);m.set_player(0,'redshirt_used_code',1)
    assert m.rows['players'][0]['redshirt_code']==0 and m.rows['players'][0]['redshirt_used_code']==1
    m.undo();assert bytes(m.data)==before
    m.set_player(0,'redshirt_used_code',1);m.set_player(0,'redshirt_code',3)
    assert m.rows['players'][0]['redshirt_used_code']==0


def test_shoe_brand_changes_normalize_only_dependent_equipment():
    m=roster();m.set_player(0,'shoe_brand_code',1);m.set_player(0,'shoe_style_code',2);m.set_player(0,'home_shoe_color_code',15);before=bytes(m.data);m.set_player(0,'shoe_brand_code',2);row=m.rows['players'][0]
    assert row['shoe_style_code']==0 and row['home_shoe_color_code']==15 and texture(row)=='shoe_200_15.iff'
    m.undo();assert bytes(m.data)==before


def test_conference_history_preserves_all_other_bytes_and_csv_roundtrips(tmp_path):
    m=roster();before=bytes(m.data);conference_history.set_value(m,1,'ncaa_titles',12);off=m.rows['conferences'][1]['offset']+0x10
    assert m.data[:off]==before[:off] and m.data[off+2:]==before[off+2:];m.undo();assert bytes(m.data)==before
    path=tmp_path/'conferences.csv';roster_csv.export(m,'conferences',path);text=path.read_text(encoding='utf-8-sig').splitlines();row=text[1].split(',');row[4]='7';text[1]=','.join(row);path.write_text('\n'.join(text)+'\n',encoding='utf-8-sig');changes=roster_csv.review(m,path);roster_csv.apply(m,changes)
    assert m.rows['conferences'][0]['ncaa_titles']==7


def test_player_detail_model_uses_dynamic_shoe_choices_and_real_qmodel_indices(qapp):
    m=roster();model=PlayerDetailsModel(m,0,category='footwear');brand=next(i for i,f in enumerate(model.fields) if f['key']=='shoe_brand_code');assert model.setData(model.index(brand,1),1)
    style=next(i for i,f in enumerate(model.fields) if f['key']=='shoe_style_code');assert len(model.choices(style))==3
