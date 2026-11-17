"""Summarize Xbox decompiled accessors; human review precedes schema promotion."""
import argparse,json,re
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('audit',type=Path);p.add_argument('candidates',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    labels={int(r['text_id'],16):r for r in json.loads(a.candidates.read_text())};result=[]
    for section in a.audit.read_text().split('caption=')[1:]:
        key=int(section[:8],16);label=labels.get(key,{})
        for match in re.finditer(r'match=([0-9a-f]+)',section):
            base=int(match[1],16)
            getter=re.search(r'^  '+f'{base+36:08x}'+r' ([0-9a-f]+) function=.*?\n(.*?)(?=^  [0-9a-f]{8}|\Z)',section[match.end():],re.M|re.S)
            if not getter:continue
            setter=re.search(r'^  '+f'{base+40:08x}'+r' ([0-9a-f]+) function=.*?\n(.*?)(?=^  [0-9a-f]{8}|\Z)',section[match.end():],re.M|re.S)
            result.append(dict(label, key=f'{key:08x}',binding=f'{base:08x}',getter=getter[1],code=getter[2].strip(),setter=setter[1] if setter else None,setter_code=setter[2].strip() if setter else None))
    a.output.write_text(json.dumps(result,indent=2));print('\n'.join(r.get('name',r['key'])+' '+r['getter']+' '+r['code'].replace('\n',' ') for r in result))
if __name__=='__main__':main()
