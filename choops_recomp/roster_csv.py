"""Source-bound roster CSV, reviewable differences and one-step batch undo."""
import csv,io,json
from pathlib import Path
from .roster import STRINGS
from .player_fields import FIELDS
from .workspace import sha


def fields(table):
    result=list(STRINGS.get(table,{}))
    if table=='players':result+=['jersey_number','height_inches','position_code',*FIELDS,*[f'rating_{i+1:02d}' for i in range(30)]]
    return result


def value(row,field):return row['ratings'][int(field[7:])-1] if field.startswith('rating_') else row[field]


def export(model,table,destination):
    destination=Path(destination);marker=destination.with_suffix(destination.suffix+'.json');columns=fields(table)
    if not columns:raise ValueError('No CSV-editable fields in this table yet')
    if destination.exists() or marker.exists():raise ValueError('Choose a new CSV destination')
    text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=['index',*columns]);writer.writeheader()
    for row in model.rows[table]:writer.writerow(dict(index=row['index'],**{key:value(row,key) for key in columns}))
    metadata=dict(version=1,platform='xbox360',table=table,source_sha256=sha(model.original),fields=columns)
    with destination.open('x',encoding='utf-8-sig',newline='') as stream:stream.write(text.getvalue())
    try:
        with marker.open('x',encoding='utf-8') as stream:json.dump(metadata,stream,indent=2)
    except BaseException:destination.unlink();raise


def review(model,source):
    source=Path(source);metadata=json.loads(source.with_suffix(source.suffix+'.json').read_text());table=metadata.get('table')
    if metadata.get('version')!=1 or metadata.get('platform')!='xbox360' or metadata.get('source_sha256')!=sha(model.original):raise ValueError('CSV belongs to a different Xbox source roster')
    columns=metadata.get('fields',[])
    if not columns or len(set(columns))!=len(columns) or not set(columns)<=set(fields(table)):raise ValueError('CSV field profile mismatch')
    changes=[];seen=set()
    with source.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['index',*columns]:raise ValueError('CSV headers changed or contain unsupported fields')
        for row in reader:
            index=int(row['index']);current=model.row(table,index)
            if index in seen:raise ValueError('Duplicate CSV row')
            seen.add(index)
            for field in columns:
                before=value(current,field);after=row[field]
                if field not in STRINGS.get(table,{}):after=float(after) if field.startswith('rating_') else int(after)
                if before!=after:changes.append(dict(table=table,index=index,field=field,before=before,after=after))
    # Validate on an independent document before any caller can apply the review.
    from .roster import Roster
    apply(Roster(model.data),changes)
    return changes


def apply(model,changes,selected_fields=None):
    with model.transaction():
        for change in changes:
            table,index,field=change['table'],change['index'],change['field']
            if selected_fields is not None and field not in selected_fields:continue
            if value(model.row(table,index),field)!=change['before']:raise ValueError('Roster changed since CSV review')
            if field in STRINGS.get(table,{}):model.set_string(table,index,field,change['after'])
            elif field.startswith('rating_'):model.set_rating(index,int(field[7:])-1,change['after'])
            else:model.set_player(index,field,change['after'])
