"""Authoritative reviewed catalogue; legacy UI fields are derived here."""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
CATALOG = BASE / 'data/catalog'
METRIC_KEYS = ('psnr', 'ssim', 'snr_gain', 'glyph_completeness', 'character_accuracy')
def load(name):
    return json.loads((CATALOG / name).read_text(encoding='utf-8'))
def adapt(record):
    r = dict(record)
    r.update(script_type=r['scriptType'],year=r['originalYear'],ganzhi='未核定',location=r.get('originalLocation') or '原碑所在地未核定',museum=r['rubbingCollectionInstitution'],dimensions=r.get('dimensions','未核定'),summary=r['description'],historical_context=r['description'],badges=[r['dynasty'],r['artifactType'],'真实馆藏'],raw_image=r['imageAssets']['readable'],clean_image=r['imageAssets']['readable'],damaged_image='',restored_image='',metrics={k:None for k in METRIC_KEYS},translation=r.get('transcription',''),inscriptionAuthor=r['author'],collectionInstitution=r['rubbingCollectionInstitution'],currentLocation=r.get('physicalCollectionInstitution') or '原石现藏机构未核定',weathering_level=r['weatheringLevel'],imageUrl=r['imageAssets']['cover'],localImagePath=r['imageAssets']['readable'].split('?')[0],gis_coords=[],isDemo=False,source_kind='verified_review_v3',catalogVersion=3)
    return r
def museum_records():return [adapt(r) for r in load('steles28.json')]
def inference(record):
    if record.get('isDemo') and record.get('inferenceDemo'):
        return record['inferenceDemo']
    text=record.get('translation','');chars=[c for c in text if '\u3400'<=c<='\u9fff'][:35]
    return {'transcript':text,'characters':[dict(id=f'c{i+1}',char=c,status='clear',col=i//7+1,row=i%7+1) for i,c in enumerate(chars)],'damaged_summary':'馆方释文参考；未执行本图残字检测或概率推演。' if text else '本件尚无核验释文；推演需提交图像区域与上下文。'}
def report(record):
    return {'ablation':[],'evaluation_summary':'未评测：未建立配对真值或消融实验记录。实际处理输出与评测结论分别保存。','scholarly_analysis':record.get('description') or record.get('summary',''),'rubbing_dimensions':record.get('dimensions','未核定'),'epigraphic_conclusion':f"《{record['title']}》以所列馆藏记录为依据；未形成新增残字定论。",'stele_id':record['id'],'title':record['title'],'sourceUrl':record.get('sourceUrl'),'metrics':{k:None for k in METRIC_KEYS}}
def graph(record):
    nodes=[dict(id='stele',name=record['title'],category='stele',value=100,symbolSize=64,desc=record.get('description',''))];links=[]
    for key,field,category,relation in [('calligrapher','calligrapher','person','书丹'),('author','inscriptionAuthor','person','撰文'),('museum','collectionInstitution','place','拓本现藏'),('era','originalYear','office','原刻纪年')]:
        value=record.get(field)
        if value and value!='未核定':
            nodes.append(dict(id=key,name=value,category=category,value=75,symbolSize=48,desc=relation));links.append(dict(source='stele',target=key,relation=relation))
    return {'nodes':nodes,'links':links,'gis_route':[],'verification':'馆藏资料关联；尚无核验地理坐标，不推造历史轨迹。'}
