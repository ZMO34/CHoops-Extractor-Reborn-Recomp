"""Xbox player footwear fields with dependent styles/colors and asset routing."""
import json
from pathlib import Path
from .player_fields import FIELDS
PROFILE=json.loads((Path(__file__).parent/'data/xbox_footwear.json').read_text(encoding='utf-8'))
BRANDS={int(k):v for k,v in PROFILE['brands'].items()}
KEYS=('shoe_brand_code','shoe_style_code','home_shoe_color_code','away_shoe_color_code')


def choices(field,player):
    if field=='shoe_brand_code':return {str(k):v['name'] for k,v in BRANDS.items()}
    brand=BRANDS.get(player['shoe_brand_code'])
    if brand is None:return {}
    if field=='shoe_style_code':return {str(i):f"Style {brand['base']+i}" for i in range(brand['styles'])}
    return {str(i):PROFILE['colors'][str(i)] for i in range(brand['colors'])}


def texture(player,away=False):
    brand=BRANDS.get(player['shoe_brand_code']);style=player['shoe_style_code'];color=player['away_shoe_color_code' if away else 'home_shoe_color_code']
    if brand is None or not 0<=style<brand['styles'] or not 0<=color<brand['colors']:raise ValueError('Xbox shoe assignment has no supported artwork')
    return f'shoe_{color}.iff' if brand['base']==0 else f"shoe_{brand['base']+style}_{color:02d}.iff"


def set_value(model,index,field,value):
    if field not in KEYS or type(value) is not int:raise ValueError('Invalid shoe field/value')
    player=dict(model.row('players',index));player[field]=value
    if field=='shoe_brand_code':
        if value not in BRANDS:raise ValueError('Unknown Xbox shoe manufacturer')
        for key in KEYS[1:]:
            if str(player[key]) not in choices(key,player):player[key]=0
    elif str(value) not in choices(field,player):raise ValueError('Choose a style/color available for this shoe manufacturer')
    texture(player);texture(player,True);data=bytearray(model.data);base=model.row('players',index)['offset']
    for key in KEYS:
        spec=FIELDS[key];off=base+spec['offset'];word=int.from_bytes(data[off:off+4],'big');mask=((1<<spec['bits'])-1)<<spec['shift'];data[off:off+4]=((word&~mask)|(player[key]<<spec['shift'])).to_bytes(4,'big')
    model._commit(data)
