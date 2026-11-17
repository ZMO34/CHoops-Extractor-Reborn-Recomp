"""Xbox relationship writes checked against live table boundaries and backlinks.

Offsets/anchor biases are verified on the supplied Xbox corpus. No saved-data
addresses or structures from another platform are used.
"""
import struct
from .roster import Roster

REFERENCES={'arena':(0x44,'arenas',25),'conference':(0x48,'conferences',1),'rival1':(0x4c,'teams',49),'rival2':(0x50,'teams',49),'rival3':(0x54,'teams',49),'coach':(0x60,'coaches',21),'assistant1':(0x64,'coaches',21),'assistant2':(0x68,'coaches',21)}
LISTS={'teams':(0x6c,18,0x188,'players',17),'conferences':(0x6e0,100,0x870,'teams',49)}


def reference(model,field,table,bias):
    delta=struct.unpack_from('>i',model.data,field)[0]
    if delta in (0,-1):return None
    start,count,stride=model.tables[table];offset=field+delta-bias-start
    if offset<0 or offset%stride or offset//stride>=count:raise ValueError('Xbox relationship does not target a valid '+table+' row')
    return offset//stride


def team_links(model,index):
    row=model.row('teams',index)
    return {name:reference(model,row['offset']+delta,table,bias) for name,(delta,table,bias) in REFERENCES.items()}


def members(model,table,index):
    delta,capacity,count_offset,target,bias=LISTS[table];offset=model.row(table,index)['offset'];count=struct.unpack_from('>H',model.data,offset+count_offset)[0]
    slots=[reference(model,offset+delta+i*4,target,bias) for i in range(capacity)]
    if count>capacity or any(v is None for v in slots[:count]) or any(v is not None for v in slots[count:]) or len(set(slots[:count]))!=count:raise ValueError('Xbox membership list/count is inconsistent or ambiguous')
    return slots[:count]


def catalog(model):
    teams=[dict(team_links(model,i),players=members(model,'teams',i)) for i in range(len(model.rows['teams']))]
    conferences=[members(model,'conferences',i) for i in range(len(model.rows['conferences']))]
    owners={};schools={}
    for i,group in enumerate(conferences):
        for team in group:
            if team in owners:raise ValueError('Team belongs to multiple conference member lists')
            owners[team]=i
    for i,row in enumerate(teams):
        if row['conference']!=owners.get(i):raise ValueError('Team and conference reciprocal membership disagree')
        for player in row['players']:schools.setdefault(player,[]).append(i)
    return dict(teams=teams,conferences=conferences,schools=schools)


def _put_reference(data,model,field,table,bias,index):
    value=0 if index is None else model.row(table,index)['offset']+bias-field
    struct.pack_into('>i',data,field,value)


def _put_members(data,model,table,index,values):
    delta,capacity,count_offset,target,bias=LISTS[table];offset=model.row(table,index)['offset']
    if len(values)>capacity or len(set(values))!=len(values):raise ValueError('Destination membership list is full or contains duplicates')
    for i in range(capacity):_put_reference(data,model,offset+delta+i*4,target,bias,values[i] if i<len(values) else None)
    struct.pack_into('>H',data,offset+count_offset,len(values))


def _commit(model,data):
    catalog(Roster(data));model._commit(data)


def assign(model,team,field,target):
    if field not in REFERENCES:raise ValueError('Unknown Xbox team relationship')
    if field=='conference':return move_conference(model,team,target)
    catalog(model);delta,table,bias=REFERENCES[field];row=model.row('teams',team)
    if target is not None:model.row(table,target)
    if field.startswith('rival') and target==team:raise ValueError('A team cannot be its own rival')
    data=bytearray(model.data);_put_reference(data,model,row['offset']+delta,table,bias,target);_commit(model,data)


def move_player(model,player,team):
    model.row('players',player);state=catalog(model);owners=state['schools'].get(player,[])
    if len(owners)>1:raise ValueError('Shared player records cannot be transferred automatically')
    if team is not None:model.row('teams',team)
    old=owners[0] if owners else None
    if old==team:return
    groups={}
    if old is not None:groups[old]=[p for p in state['teams'][old]['players'] if p!=player]
    if team is not None:groups[team]=state['teams'][team]['players']+[player]
    data=bytearray(model.data)
    for index,values in groups.items():_put_members(data,model,'teams',index,values)
    _commit(model,data)


def reorder_player(model,team,player,destination):
    state=catalog(model);group=list(state['teams'][team]['players'])
    if player not in group or not isinstance(destination,int) or not 0<=destination<len(group):raise ValueError('Invalid roster lineup position')
    group.remove(player);group.insert(destination,player);data=bytearray(model.data);_put_members(data,model,'teams',team,group);_commit(model,data)


def move_conference(model,team,conference):
    model.row('teams',team)
    if conference is not None:model.row('conferences',conference)
    state=catalog(model);old=state['teams'][team]['conference']
    if old==conference:return
    groups={}
    if old is not None:groups[old]=[t for t in state['conferences'][old] if t!=team]
    if conference is not None:groups[conference]=state['conferences'][conference]+[team]
    data=bytearray(model.data)
    for index,values in groups.items():_put_members(data,model,'conferences',index,values)
    _put_reference(data,model,model.row('teams',team)['offset']+0x48,'conferences',1,conference);_commit(model,data)
