"""Idempotent scoped migration; preserve user data and historical references."""
import argparse,json,sys,sqlite3,shutil
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from catalog import museum_records,load
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def migrate(base=BASE,backup=True):
    rows=museum_records();active={r['id'] for r in rows};retired={r['oldId'] for r in load('replacement_mapping.json')}
    db=base/'data/museum_database.json';existing=json.loads(db.read_text('utf-8')) if db.exists() else []
    backupdir=base/'data/runtime/museum-v3/backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    if backup:
        for name in ['data/museum_database.json','data/museum_database_backup.json','data/museum-import/merged_28_steles.json','apps/web/src/data/steles28.json','data/museum-images/import_image_status.json']:
            p=base/name
            if p.exists():
                t=backupdir/name;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t)
    old={r['id']:r for r in existing};archive={r['id']:r for r in load('retired_steles.json')}
    archivepath=base/'data/catalog/retired_database_records.json'
    if archivepath.exists():archive.update({r['id']:r for r in json.loads(archivepath.read_text('utf-8'))})
    archive.update({id:old[id] for id in retired if id in old});dump(archivepath,list(archive.values()))
    extras=[r for r in existing if r['id'] not in active|retired];dump(db,rows+extras)
    for name in ['data/museum-import/merged_28_steles.json','apps/web/src/data/steles28.json']:dump(base/name,rows)
    dump(base/'data/museum-images/import_image_status.json',{r['id']:{'status':r['imageStatus'],'imageAssets':r['imageAssets']} for r in rows})
    sqlite=base/'data/rubbingmind.sqlite';sqlcounts={'updated':0,'added':0,'retainedRetired':0}
    if sqlite.exists():
        with sqlite3.connect(sqlite) as conn:
            if backup:
                backupdir.mkdir(parents=True,exist_ok=True)
                with sqlite3.connect(backupdir/'rubbingmind.sqlite') as dest:conn.backup(dest)
            if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steles'").fetchone():
                columns={r[1] for r in conn.execute('PRAGMA table_info(steles)')};present={r[0] for r in conn.execute('SELECT id FROM steles')}
                for r in rows:
                    values={k:v for k,v in r.items() if k in columns and not isinstance(v,(list,dict))}
                    values.update(source_url=r['sourceUrl'],image_status=r['imageStatus'],metrics_json=json.dumps(r['metrics']),gis_lng=None,gis_lat=None);values={k:v for k,v in values.items() if k in columns}
                    keys=list(values);update=','.join(f'{k}=excluded.{k}' for k in keys if k!='id')
                    conn.execute(f"INSERT INTO steles ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)}) ON CONFLICT(id) DO UPDATE SET {update}",[values[k] for k in keys]);sqlcounts['updated' if r['id'] in present else 'added']+=1
                sqlcounts['retainedRetired']=len(present&retired)
                conn.execute('CREATE TABLE IF NOT EXISTS museum_catalog_status (id TEXT PRIMARY KEY,status TEXT NOT NULL,recommended_id TEXT)')
                for r in rows:conn.execute("INSERT OR REPLACE INTO museum_catalog_status VALUES (?,'active',NULL)",(r['id'],))
                for r in load('replacement_mapping.json'):conn.execute("INSERT OR REPLACE INTO museum_catalog_status VALUES (?,'retired',?)",(r['oldId'],r['newId']))
    result=dict(updated=len(active&set(old)),added=len(active-set(old)),archived=len(retired&set(old)),preservedUserRecords=len(extras),failed=0,sqlite=sqlcounts);dump(base/'data/runtime/museum-v3/migration_result.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--no-backup',action='store_true');args=p.parse_args();print(json.dumps(migrate(backup=not args.no_backup),ensure_ascii=False))
