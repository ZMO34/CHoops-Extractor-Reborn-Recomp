"""Read-only validation of candidate relationship layouts on Xbox bytes."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from choops_recomp.workspace import Workspace
from choops_recomp.roster import Roster

REFERENCES={'arena':(0x44,'arenas',25),'conference':(0x48,'conferences',1),'rival1':(0x4c,'teams',49),'rival2':(0x50,'teams',49),'rival3':(0x54,'teams',49),'coach':(0x60,'coaches',21),'assistant1':(0x64,'coaches',21),'assistant2':(0x68,'coaches',21)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',required=True);a=p.parse_args();w=Workspace(a.assets);m=Roster(w.of_type('ROST')[0].blocks()[0]);result={}
    for name,(delta,table,bias) in REFERENCES.items():
        start,count,stride=m.tables[table];valid=[];null=[];bad=[]
        for row in m.rows['teams']:
            field=row['offset']+delta;value=struct.unpack_from('>i',m.data,field)[0]
            if value in (0,-1):null.append(row['index']);continue
            target=field+value-start-bias
            (valid if target%stride==0 and 0<=target//stride<count else bad).append((row['index'],target//stride))
        result[name]=dict(valid=len(valid),null=len(null),bad=bad)
    Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
