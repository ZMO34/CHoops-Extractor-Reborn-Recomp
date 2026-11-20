"""Xbox conference historical scalars; reciprocal membership is separate."""
import struct
FIELDS={'founded_year':dict(offset=0x0e,minimum=0,maximum=9999,name='Founded year'),'ncaa_titles':dict(offset=0x10,minimum=0,maximum=65535,name='NCAA championships'),'ncaa_final_fours':dict(offset=0x12,minimum=0,maximum=65535,name='NCAA Final Fours'),'previous_year_bids':dict(offset=0x14,minimum=0,maximum=100,name='Previous-year bids')}


def read(data,offset):return {key:struct.unpack_from('>H',data,offset+spec['offset'])[0] for key,spec in FIELDS.items()}


def set_value(model,index,field,value):
    spec=FIELDS.get(field)
    if spec is None or type(value) is not int or not spec['minimum']<=value<=spec['maximum']:raise ValueError('Conference history value outside supported range')
    data=bytearray(model.data);struct.pack_into('>H',data,model.row('conferences',index)['offset']+spec['offset'],value);model._commit(data)
