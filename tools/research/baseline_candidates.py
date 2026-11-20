"""Extract caption-search candidates, never source-platform offsets/addresses."""
import ast,json,argparse
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();rows=[]
    rating_names=()
    for filename in ('schema.py','appearance.py'):
        tree=ast.parse((a.source/'choops_py/roster'/filename).read_text())
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RATING_NAMES' for t in node.targets):rating_names=ast.literal_eval(node.value)
        for node in ast.walk(tree):
            if not isinstance(node,ast.Dict):continue
            try:item=ast.literal_eval(node)
            except (ValueError,TypeError):continue
            if isinstance(item,dict) and 'text_id' in item:
                entry={k:item[k] for k in ('name','text_id') if k in item}
                if 'name' not in entry and 'offset' in item and rating_names:entry['name']=rating_names[(item['offset']-60)//2];entry['kind']='rating'
                rows.append(entry)
    unique={int(r['text_id'],16):r for r in rows}
    a.output.write_text('\n'.join(f'{key:08x}' for key in unique)+'\n')
    a.output.with_suffix('.json').write_text(json.dumps(list(unique.values()),indent=2))
    print(f'{len(unique)} caption candidates; no offsets or executable addresses exported')
if __name__=='__main__':main()
