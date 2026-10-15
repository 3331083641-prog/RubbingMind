import sys,json,sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from main import app
from catalog import load,museum_records
from scripts.validate_museum_v3 import validate
from scripts.migrate_museum_v3 import migrate

def test_reviewed_assets_and_exports():assert validate()['sha256Match']==84

def test_all_identities_in_api():
    client=TestClient(app)
    assert client.get('/api/steles').json()==museum_records()
    for r in museum_records():
        assert client.get('/api/steles/'+r['id']).json()==r
        report=client.get('/api/steles/'+r['id']+'/report').json()
        assert report['title']==r['title'] and report['ablation']==[]
        graph=client.get('/api/steles/'+r['id']+'/graph').json()
        assert graph['nodes'][0]['name']==r['title'] and graph['gis_route']==[]
    assert client.get('/api/steles/no-such-id').status_code==404
    for r in load('replacement_mapping.json'):
        res=client.get('/api/steles/'+r['oldId']);assert res.status_code==410
        assert res.json()['detail']['recommendedId']==r['newId']
    for core in load('core_samples.json'):
        assert client.get('/api/steles/'+core['id']).json()['id']==core['id']
    assert client.get('/api/steles/qing_02_chongli_wushi').json()['id']=='qing_02_wushi_reerection'

def test_replacement_identity_details():
    rows={r['id']:r for r in museum_records()}
    expected=[('yuan_04_jingyuanchang','赵孟頫书敬元长墓碣铭','贈拓000412','34668'),('qing_01_qianlong_heart_sutra','乾隆御书般若波罗蜜多心经','y1958-220','57606'),('qing_02_wushi_reerection','重立武氏祠石记','y1957-139 b','57837'),('qing_03_sanxitang_preface','御刻三希堂石渠宝笈法帖·乾隆御序','1984.496.1–.32（首册御序）','36142'),('qing_04_ayuwang_reliquary','阿育王寺舍利塔碑','y1958-279','57684')]
    for id,title,number,urlid in expected:
        r=rows[id];assert r['title']==title and r['collectionNumber']==number and urlid in r['sourceUrl']
    assert rows['qing_02_wushi_reerection']['originalYearCE']==1787

def test_migration_preserves_user_data_and_history(tmp_path):
    path=tmp_path/'data/museum_database.json';path.parent.mkdir(parents=True)
    custom={'id':'custom-preserved','title':'用户上传','raw_image':'user.png'}
    retired=load('retired_steles.json')[0]
    path.write_text(json.dumps([custom,retired]),'utf-8')
    db=tmp_path/'data/rubbingmind.sqlite'
    with sqlite3.connect(db) as c:
        c.execute('CREATE TABLE steles (id TEXT PRIMARY KEY,title TEXT,dynasty TEXT,dynasty_value TEXT,author TEXT,source_url TEXT,metrics_json TEXT)')
        c.execute('INSERT INTO steles VALUES (?,?,?,?,?,?,?)',(retired['id'],retired['title'],'元代','yuan','','','{}'))
        c.execute('INSERT INTO steles VALUES (?,?,?,?,?,?,?)',('custom-preserved','用户上传','','','','','{}'))
        c.execute('CREATE TABLE restoration_logs (id INTEGER PRIMARY KEY,stele_id TEXT,note TEXT)')
        c.execute('INSERT INTO restoration_logs VALUES (1,?,?)',(retired['id'],'用户原实验'))
    first=migrate(tmp_path);second=migrate(tmp_path)
    assert first['added']==28 and second['added']==0 and second['updated']==28
    assert first['preservedUserRecords']==second['preservedUserRecords']==1
    assert json.loads(path.read_text('utf-8'))[-1]==custom
    with sqlite3.connect(db) as c:
        assert c.execute('SELECT COUNT(*) FROM steles').fetchone()[0]==30
        assert c.execute('SELECT stele_id,note FROM restoration_logs').fetchone()==(retired['id'],'用户原实验')
        assert c.execute("SELECT COUNT(*) FROM museum_catalog_status WHERE status='active'").fetchone()[0]==28

def test_real_processing_uses_selected_image_and_saves_result(monkeypatch,tmp_path):
    import museum_processing
    import base64
    from io import BytesIO
    from PIL import Image
    buf=BytesIO();Image.new('RGB',(4,4)).save(buf,format='PNG');encoded=base64.b64encode(buf.getvalue()).decode()
    class Engine:
        def process_rubbing(self,**kwargs):
            assert 'qing_02_wushi_reerection_readable.jpg' in kwargs['image_input']
            return {'restored_b64':encoded,'metrics':{'elapsed_ms':1,'psnr':None},'diagnostic_metrics':{'input_output_mean_absolute_difference':2.5}}
    from main import ProcessRequest
    from museum_manager import museum_manager
    import shutil
    source = ROOT / 'apps/web/public/assets/stele/museum-rubbings/qing_02_wushi_reerection_readable.jpg'
    input_copy = tmp_path / 'apps/web/public/assets/stele/museum-rubbings/qing_02_wushi_reerection_readable.jpg'
    input_copy.parent.mkdir(parents=True)
    shutil.copyfile(source, input_copy)
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    result=museum_processing.process_verified_request(ProcessRequest(stele_id='qing_02_wushi_reerection'),museum_manager,Engine())
    assert result['stele_id']=='qing_02_wushi_reerection' and result['psnr'] is None
    assert (tmp_path/result['restored_image'].lstrip('/')).is_file()
    assert result['engineDiagnosticMetrics']['input_output_mean_absolute_difference']==2.5
    run_id=result['runId']
    client=TestClient(app)
    history=client.get('/api/steles/qing_02_wushi_reerection/runs').json()
    assert history[0]['runId']==run_id
    assert history[0]['inputImageSha256'] and history[0]['outputSha256']['restored']
    report=client.get(f'/api/steles/qing_02_wushi_reerection/report?run_id={run_id}').json()
    assert report['run']['runId']==run_id and report['run']['evaluationStatus']=='unassessed'
    assert report['reportId'].endswith(run_id)
    assert client.delete(f'/api/steles/qing_02_wushi_reerection/runs/{run_id}').status_code==400
    assert client.delete(f'/api/steles/qing_02_wushi_reerection/runs/{run_id}?confirm=true').status_code==200
    assert client.get('/api/steles/qing_02_wushi_reerection/runs').json()==[]
