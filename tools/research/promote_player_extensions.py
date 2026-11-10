"""Promote reviewed Xbox class/eligibility/jumper consumers and localized tables."""
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace
from choops_recomp.localization import entries,literal


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--audit-directory',type=Path,required=True);args=p.parse_args();root=args.audit_directory
    callbacks=(root/'eligibility-history-fields.txt').read_text();jumper=(root/'shoe-shooting-fields.txt').read_text();classes=(root/'player-next-audit.txt').read_text();tables=(root/'extended-player-tables-audit.txt').read_text()
    for fragment in ('0x2000000','0xfdffffff','0x18','0xfeffffff','0xfffe7fff'):assert fragment in callbacks,fragment
    assert '0xffe1ffff' in classes and '0x84' in classes
    assert 'param_1 + 0x74' in jumper and '84841f40' in jumper
    words={int(a,16):int(v,16) for a,v in re.findall(r'^([0-9a-f]{8}) ([0-9a-f]{8})',tables,re.M)}
    workspace=Workspace(args.assets);loc=entries(workspace.resource('hash_bd1ab121.iff/0').blocks()[0]);choices=lambda base,count:{str(i):literal(loc[words[base+i*4]]) for i in range(count)}
    fields=[dict(key='class_code',name='Class',offset=0x94,size=4,shift=17,bits=4,minimum=0,maximum=8,getter='84757078',setter='84c7d500',text_id='181a20c5',choices=choices(0x84f99440,9),menu_ranges=dict(college=[4,7],recruit=[0,5])),dict(key='scholarship_code',name='Scholarship',offset=0x9c,size=4,shift=25,bits=1,minimum=0,maximum=1,getter='84c7cf98',setter='84c7d048',text_id='360fda01',choices={'0':'No','1':'Yes'}),dict(key='redshirt_code',name='Redshirt',offset=0x94,size=4,shift=15,bits=2,minimum=0,maximum=3,getter='84c7d1c0',setter='84c7d208',text_id='828bb5ab',choices=choices(0x8554f238,4),clears_when_nonzero='redshirt_used_code'),dict(key='redshirt_used_code',name='Redshirt Used',offset=0x9c,size=4,shift=24,bits=1,minimum=0,maximum=1,getter='84c7d348',setter='84c7d3f8',text_id='4977988d',choices={'0':'No','1':'Yes'},clears_when_nonzero='redshirt_code')]
    section=re.search(r'caption=3479c0ed\n(.*?)(?=caption=|\Z)',jumper,re.S)[1];options={int(i):literal(loc[int(ident,16)]) for i,ident in re.findall(r'^option=(\d+) id=([0-9a-f]{8})',section,re.M)}
    assert len(options)==112 and all(options.values())
    fields.append(dict(key='jumper_code',name='Jumper',offset=0x84,size=1,shift=0,bits=8,minimum=0,maximum=111,getter='84841f30',setter='84841f40',text_id='3479c0ed',choices=options))
    tendencies=(root/'player-potential-audit.txt').read_text()
    for i,(key,ident,getter,setter) in enumerate([('close_shots_tendency','be1a55fb','847528b8','84841ed0'),('midrange_shots_tendency','065ff1d3','847528c0','84841ed8'),('three_point_shots_tendency','441a8f9f','847528c8','84841ee0'),('drive_lane_tendency','6a87972f','847528d0','84841ee8')]):
        section=re.search('caption='+ident+r'\n(.*?)(?=caption=|\Z)',tendencies,re.S)[1];assert getter in section and setter in section and f'param_1 + 0x{0x68+i:x}' in section
        fields.append(dict(key=key,name=literal(loc[int(ident,16)]),offset=0x78+i,size=1,shift=0,bits=8,minimum=0,maximum=99,getter=getter,setter=setter,text_id=ident,group='tendencies'))
    shoe=(root/'shoe-getter-audit.txt').read_text()
    for fragment in ('0xff07ffff','0xfff83fff','0xffffc1ff','0xffc7ffff'):assert fragment in shoe
    for key,name,offset,shift,bits,maximum,getter,setter in [('shoe_brand_code','Shoe manufacturer',0xa8,19,3,4,'84842738','84842748'),('shoe_style_code','Shoe style',0xa0,19,5,3,'84842638','84842648'),('home_shoe_color_code','Home shoe color',0xa0,14,5,15,'84842658','84842668'),('away_shoe_color_code','Away shoe color',0xa0,9,5,15,'84842678','84842688')]:fields.append(dict(key=key,name=name,offset=offset,size=4,shift=shift,bits=bits,minimum=0,maximum=maximum,getter=getter,setter=setter,group='footwear'))
    from choops_recomp.shoe_preview import available
    assert len(available(workspace))==90
    colors=choices(0x85551fc8,16);brands={0:dict(name='Generic',base=0,styles=2,colors=2),1:dict(name='Nike',base=100,styles=3,colors=16),2:dict(name='Reebok',base=200,styles=1,colors=16),3:dict(name='Adidas',base=300,styles=1,colors=16),4:dict(name='Special / Jordan artwork',base=500,styles=4,colors=2)}
    directory=Path(__file__).resolve().parents[2]/'choops_recomp/data';(directory/'xbox_footwear.json').write_text(json.dumps(dict(version=1,platform='xbox360',brands=brands,colors=colors),indent=2)+'\n',encoding='utf-8')
    target=directory/'xbox_player_fields.json';profile=json.loads(target.read_text());merged={f['key']:f for f in profile['fields']};merged.update({f['key']:f for f in fields});profile['fields']=list(merged.values());profile['version']=2
    assert all(all(v is not None for v in f.get('choices',{}).values()) for f in fields)
    target.write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8');print('Promoted reviewed Xbox player extensions; total',len(profile['fields']))


if __name__=='__main__':main()
