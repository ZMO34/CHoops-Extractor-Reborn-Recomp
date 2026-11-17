import struct
import pytest
from choops_recomp.roster import Roster,TABLES
from choops_recomp import relationships as links


def roster(players=5):
    data=bytearray(256);counts=dict(players=players,teams=2,arenas=2,coaches=6,conferences=2,uniforms=4)
    starts={}
    for table,(field,bias,stride,limit) in TABLES.items():
        start=len(data);starts[table]=start;data.extend(bytes(counts[table]*stride+64));struct.pack_into('>Ii',data,field,counts[table],start-(field+4)+bias)
    model=Roster(data)
    for team in range(2):
        off=model.row('teams',team)['offset']
        for name,(delta,table,bias) in links.REFERENCES.items():links._put_reference(data,model,off+delta,table,bias,team)
        links._put_members(data,model,'teams',team,[0,1] if team==0 else [2])
        links._put_members(data,model,'conferences',team,[team])
    return Roster(data)


def test_transfer_updates_lists_counts_and_is_one_undo():
    m=roster();before=bytes(m.data);links.move_player(m,1,1)
    assert links.members(m,'teams',0)==[0] and links.members(m,'teams',1)==[2,1]
    allowed=set()
    for r in m.rows['teams']:
        off=r['offset'];allowed.update(range(off+0x6c,off+0x6c+72));allowed.update(range(off+0x188,off+0x18a))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,m.data)))
    assert len(m.history)==1;m.undo();assert bytes(m.data)==before


def test_conference_move_updates_reciprocal_links_and_preserves_history():
    m=roster();before=bytes(m.data);links.move_conference(m,0,1);state=links.catalog(m)
    assert state['teams'][0]['conference']==1 and state['conferences']==[[],[1,0]]
    for r in m.rows['conferences']:
        off=r['offset'];assert m.data[off:off+0x6e0]==before[off:off+0x6e0];assert m.data[off+0x872:off+2964]==before[off+0x872:off+2964]
    m.undo();assert bytes(m.data)==before


def test_assignment_writes_only_checked_reference():
    m=roster();before=bytes(m.data);links.assign(m,0,'coach',5);offset=m.rows['teams'][0]['offset']+0x60
    assert links.team_links(m,0)['coach']==5
    assert m.data[:offset]==before[:offset] and m.data[offset+4:]==before[offset+4:]
    with pytest.raises(ValueError):links.assign(m,0,'rival1',0)


def test_inconsistent_membership_rejects_without_edit():
    m=roster();off=m.rows['teams'][0]['offset'];struct.pack_into('>H',m.data,off+0x188,3);before=bytes(m.data)
    with pytest.raises(ValueError,match='inconsistent'):links.move_player(m,1,1)
    assert bytes(m.data)==before and not m.history


def test_unassignment_and_lineup_order():
    m=roster();links.reorder_player(m,0,1,0);assert links.members(m,'teams',0)==[1,0]
    links.move_player(m,1,None);assert links.catalog(m)['schools'].get(1) is None
    links.move_conference(m,0,None);assert links.catalog(m)['teams'][0]['conference'] is None


def test_full_destination_and_shared_player_reject_without_partial_changes():
    m=roster(19);data=bytearray(m.data);links._put_members(data,m,'teams',0,[18]);links._put_members(data,m,'teams',1,list(range(18)));m=Roster(data);before=bytes(m.data)
    with pytest.raises(ValueError,match='full'):links.move_player(m,18,1)
    assert bytes(m.data)==before and not m.history
    data=bytearray(m.data);links._put_members(data,m,'teams',0,[0,18]);m=Roster(data);before=bytes(m.data)
    with pytest.raises(ValueError,match='Shared'):links.move_player(m,0,None)
    assert bytes(m.data)==before
