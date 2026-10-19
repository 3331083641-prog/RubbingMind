"""Local extractive GraphRAG: Chinese FTS5/BM25 + sourced one-hop expansion.

No language model is needed or implicitly called. Generated summaries contain
only selected evidence sentences; no retrieved document is an instruction.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from catalog import BASE, load, transcription_text
from history_graph import CORE_IDS, ALIASES, resolve_id

INDEX=BASE/'data/runtime/evidence-v2.sqlite'
# Calibrated 2026-10-19: max BM25 over 15 unrelated queries = 9.647; see CONTENT_CHANGELOG (relevance threshold).
WEAK_BM25_THRESHOLD=10.0
WEAK_LABEL='弱相关，仅供参考'
VERSION='fts5-evidence-graph-v2.7'

# Traditional/variant -> simplified folding for matching only (C-15). Stored text is never rewritten.
# 徵→征 follows the simplified form used for personal names (魏征/文征明); 宫商角徵羽 is not in scope.
VARIANT_FOLD=str.maketrans({
    '徵':'征','寶':'宝','應':'应','銘':'铭','誌':'志','顏':'颜','眞':'真','書':'书','歐':'欧','陽':'阳','詢':'询',
    '禮':'礼','宮':'宫','張':'张','龍':'龙','孫':'孙','趙':'赵','鄧':'邓','東':'东','漢':'汉','劉':'刘','廟':'庙',
    '師':'师','經':'经','門':'门','萬':'万','壽':'寿','國':'国','雲':'云','興':'兴','華':'华','懷':'怀','誦':'诵',
    '義':'义','銅':'铜','記':'记','聖':'圣','長':'长','觀':'观','黨':'党','製':'制','贊':'赞','讚':'赞','權':'权',
    '時':'时','釋':'释','夢':'梦','體':'体','陸':'陆','獻':'献','無':'无','羅':'罗','綱':'纲','吳':'吴','學':'学',
    '題':'题','勳':'勋','勛':'勋','錄':'录','鄭':'郑','誰':'谁','麼':'么','麽':'么','裏':'里','裡':'里','現':'现',
    '處':'处','歲':'岁','載':'载','譔':'撰','額':'额','鐫':'镌','後':'后','與':'与','爲':'为','為':'为','嗎':'吗',
    '傳':'传','實':'实','購':'购','贈':'赠','藥':'药','鐵':'铁','碣':'碣','祐':'祐','頫':'頫','岑':'岑',
    '徐':'徐','裴':'裴','邵':'邵','蔡':'蔡','翁':'翁','鄉':'乡','縣':'县','鄴':'邺','郃':'郃','鎮':'镇','樓':'楼',
})


def fold(text):
    return str(text or '').translate(VARIANT_FOLD)


def _work_aliases():
    path=BASE/'data/catalog/work_aliases.json'
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding='utf-8'))['aliases']


def canonical_id(stele_id):
    """Collection id that evidence is filed under (demo -> same-work rubbing, review alias -> target)."""
    if not stele_id:
        return stele_id
    return resolve_id(stele_id)['evidenceId']


def tokens(text):
    chars=re.findall(r'[\u3400-\u9fff]|[a-zA-Z0-9_-]+',text.lower())
    return list(dict.fromkeys(chars+[a+b for a,b in zip(chars,chars[1:]) if len(a)==len(b)==1]))


def corpus():
    records=[];nodes=[];edges=[];places=[]
    def add(source_id,stele_id,title,text,url,institution,location,level='catalogue_record',license=None,provenance=None):
        if provenance and provenance.get('kind')=='synthetic_test_text':
            # Synthetic generator text must carry its label wherever it is retrieved.
            text='【'+provenance['label']+'】'+text
        record={'sourceId':source_id,'steleId':stele_id,'title':title,'text':text,'url':url,
            'institution':institution,'evidenceLevel':level,'originalPosition':location,'license':license,
            'origin':'reviewed_local_record','textSha256':hashlib.sha256(text.encode()).hexdigest()}
        if provenance:
            record['textProvenance']=provenance
        records.append(record)
    for r in load('steles28.json'):
        sid=r['id'];eid='catalog:'+sid
        facts=f"{r['title']}。原刻朝代：{r['dynasty']}；原刻年代：{r['originalYear']}；拓本年代：{r['rubbingPeriod']}；文物类型：{r['artifactType']}；{_role_fact(r,'author','撰文')}；{_role_fact(r,'calligrapher','书丹')}；{_role_fact(r,'titleCalligrapher','篆额')}；{_role_fact(r,'engraver','刻工')}；{_role_fact(r,'steleSubject','碑主或墓主')}；拓本现藏机构：{r['rubbingCollectionInstitution']}；拓本馆藏编号：{r['collectionNumber']}；原石现藏机构：{r.get('physicalCollectionInstitution') or '未核定'}；原碑所在地：{r.get('originalLocation') or '未核定'}。"
        add(eid,sid,r['title']+' · 馆藏著录',facts,r['sourceUrl'],r['rubbingCollectionInstitution'],'data/catalog/steles28.json#'+sid,license=r['license'])
        nodes.append({'id':sid,'name':r['title'],'category':'work','steleId':sid,'sourceIds':[eid]})
        # A work, its physical stone, and a particular collected rubbing are distinct.
        for key,name,category,relation in [('stone',r['title']+'原石','stone','原刻'),('rubbing',r['collectionNumber']+'拓本','rubbing','拓本见证'),
            ('year',r['originalYear'],'date','原刻纪年'),('collection',r['rubbingCollectionInstitution'],'institution','拓本现藏')]:
            target=sid+':'+key;nodes.append({'id':target,'name':name,'category':category,'steleId':sid,'sourceIds':[eid]})
            edges.append({'source':sid+':rubbing' if key=='collection' else sid,'target':target,'relation':relation,'sourceIds':[eid],'sourceUrl':r['sourceUrl']})
        for key,relation in [('author','撰文'),('calligrapher','书丹'),('titleCalligrapher','篆额'),('engraver','刻工'),('steleSubject','碑主或墓主')]:
            if r.get(key+'Verification')=='verified' and r.get(key) and not str(r.get(key)).startswith('未核定'):
                target=sid+':'+key;nodes.append({'id':target,'name':r[key],'category':'person','steleId':sid,'sourceIds':[eid]})
                edges.append({'source':sid,'target':target,'relation':relation,'sourceIds':[eid],'sourceUrl':r['sourceUrl']})
        text=transcription_text(r)
        # Archival extraction includes license/admin appendix; don't treat it as inscription.
        text=text.split('授權與引用')[0].split('License and attribution')[0]
        for i in range(0,len(text),500):
            if text[i:i+500].strip():add(f'{eid}:transcript:{i}',sid,r['title']+' · 馆方释文摘录',text[i:i+500],r['sourceUrl'],r['rubbingCollectionInstitution'],f"{r['sourceVerification'].get('evidenceFile')}#transcription:{i}",'archival_transcription',r['license'])
    reverse={v:k for k,v in ALIASES.items()}
    sources={r['id']:r for r in json.loads((BASE/'data/history/sources.json').read_text('utf8'))}
    for core_id in CORE_IDS:
        h=json.loads((BASE/'data/history'/f'{core_id}.json').read_text('utf8'));sid=reverse.get(core_id,core_id)
        source_ids=[]
        for source_id in h['sourceIds']:
            s=sources[source_id];eid=f'history:{core_id}:{source_id}'
            add(eid,sid,s['title'],f"{h['formalName']}。{h['identity']}。原刻/样本标签：{h['eraName']}；拓本年代：{h['rubbingPeriod']}；原石现藏：{h['originalStoneCollection']}；数字拓本：{h['digitalRubbingCollection']}；编号：{h['collectionNumber']}。相关作者：{'；'.join(h['authors'])}。{s.get('notes','')}",s['url'],s['institution'],f'data/history/{core_id}.json',
                'identity_unverified' if core_id=='wei-jianyi' else 'curated_source_summary',provenance=h.get('textProvenance'))
            source_ids.append(eid)
        for node in h['nodes']:
            nodes.append({'id':core_id+':'+node['id'],'name':node['name'],'category':node['category'],'steleId':sid,
                          'sourceIds':[f'history:{core_id}:{s}' for s in node.get('sourceIds',[]) if s in h['sourceIds']] or source_ids})
        for i,edge in enumerate(h['links']):
            sids=[f'history:{core_id}:{s}' for s in edge.get('sourceIds',[]) if s in h['sourceIds']]
            if not sids:continue
            eid=f'history:{core_id}:relation:{i}'
            node_map={n['id']:n for n in h['nodes']}
            text=f"{node_map[edge['source']]['name']} → {edge['relation']} → {node_map[edge['target']]['name']}。{node_map[edge['target']]['desc']}"
            add(eid,sid,h['formalName']+' · '+edge['relation'],text,edge['sourceUrl'],'项目已核史料摘记',f'data/history/{core_id}.json#links/{i}',
                'identity_unverified' if core_id=='wei-jianyi' else 'sourced_relationship',provenance=h.get('textProvenance'))
            edges.append({'source':core_id+':'+edge['source'],'target':core_id+':'+edge['target'],'relation':edge['relation'],'sourceIds':[eid],
                          'sourceUrl':edge['sourceUrl'],'verification':edge['verification']})
        for place in h['locations']:
            if place['verified']:
                places.append({**place,'steleId':sid,'coreSampleId':core_id})
    return records,nodes,edges,places


def fingerprint():
    paths=[BASE/'data/catalog/steles28.json',*sorted((BASE/'data/history').glob('*.json'))]
    return hashlib.sha256((''.join(hashlib.sha256(p.read_bytes()).hexdigest() for p in paths)+VERSION).encode()).hexdigest()


def ensure_index():
    INDEX.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(INDEX,timeout=20)) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY,value TEXT)')
        current=conn.execute("SELECT value FROM metadata WHERE key='fingerprint'").fetchone()
        if current and current[0]==fingerprint():return
        records,nodes,edges,places=corpus()
        with conn:
            conn.execute('DROP TABLE IF EXISTS evidence_fts')
            conn.execute('DROP TABLE IF EXISTS evidence')
            conn.execute('CREATE TABLE evidence (source_id TEXT PRIMARY KEY, stele_id TEXT, record_json TEXT)')
            conn.execute('CREATE VIRTUAL TABLE evidence_fts USING fts5(source_id UNINDEXED, title, body, tokenize="unicode61")')
            for r in records:
                conn.execute('INSERT INTO evidence VALUES (?,?,?)',(r['sourceId'],r['steleId'],json.dumps(r,ensure_ascii=False)))
                body=r['text']
                label=(r.get('textProvenance') or {}).get('label')
                if label:
                    # The display label must not change ranking; index the original text only.
                    body=body.removeprefix('【'+label+'】')
                conn.execute('INSERT INTO evidence_fts VALUES (?,?,?)',(r['sourceId'],' '.join(tokens(r['title'])),' '.join(tokens(body))))
            for key,value in [('fingerprint',fingerprint()),('graph',json.dumps({'nodes':nodes,'edges':edges,'places':places},ensure_ascii=False))]:
                conn.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',(key,value))


FACETS=(
    ('撰文者','author',('撰文者','撰文','作者')),
    ('书丹者','calligrapher',('书丹者','书丹')),
    ('篆额者','titleCalligrapher',('篆额者','篆额','题额')),
    ('碑主或墓主','steleSubject',('墓主','碑主')),
    ('刻工','engraver',('刻工','镌刻')),
    ('原刻年代','originalYear',('原刻年代','原刻于','原刻纪年')),
    ('拓本年代','rubbingPeriod',('拓本年代','拓本时代')),
    ('原石保存地','physicalCollectionInstitution',('原石保存','原石现藏','原碑所在')),
    ('拓本收藏机构','rubbingCollectionInstitution',('拓本收藏','收藏机构','现藏机构','拓本现藏')),
)
PROPOSITION_STOP={'什么','谁','何人','相同','一样','不同','已经','如何','多少','哪位','哪个','哪里'}
# 碑主/墓主 is recognised but not judged: catalogue statuses are uneven and not checked against the inscriptions (C-04).
UNSUPPORTED_FACETS={'碑主或墓主'}
ASKING_WORDS=('是谁','是什么','何人','哪一','多少','哪里','在哪','何处','哪年','哪位')
# Fields compared across the catalogue and the curated history documents (C-05).
CROSS_SOURCE_FIELDS={'physicalCollectionInstitution':'originalStoneCollection','rubbingPeriod':'rubbingPeriod',
                     'rubbingCollectionInstitution':'digitalRubbingCollection'}
UNKNOWN_PREFIXES=('未核定','未核实','待考','年代待考','未确认','待评估','待核')


def _role_fact(record, field, label):
    value=str(record.get(field) or '未核定').strip()
    status=record.get(field+'Verification','unknown')
    if status=='verified' and value and not value.startswith('未核定'):
        return f'{label}：{value}'
    if status=='pending_review' and value and not value.startswith('未核定'):
        return f'{label}：{value}（待复核，不是已核定）'
    if status=='disputed':
        return f'{label}：存在争议，未核定'
    return f'{label}：未核定'


def _verified_fact(value):
    if value is None:
        return None
    text=str(value).strip()
    if not text or text.startswith('未核定') or text in ('未确认','待评估'):
        return None
    return text


def _catalogue_value(record, field):
    if not field:
        return None
    status_field=field+'Verification'
    if status_field in record and record.get(status_field)!='verified':
        return None
    return _verified_fact(record.get(field))


def _entity_tokens(value):
    return [part for part in re.split(r'[、，,；;／/\s]+', value) if part]


def _year_digits(text):
    match=re.fullmatch(r'(\d{3,4})年?', text.strip())
    return match.group(1) if match else None


def _same_recorded_value(proposed, value):
    """Exact catalogue token match. A shorter name inside a longer name is not the same person.
    Variant/traditional forms that fold to the same characters count as the same value."""
    if proposed == value or fold(proposed) == fold(value):
        return True
    tokens=_entity_tokens(value)
    if proposed in tokens or fold(proposed) in {fold(t) for t in tokens}:
        return True
    proposed_year=_year_digits(proposed)
    if proposed_year and any(_year_digits(token)==proposed_year for token in [value, *tokens]):
        return True
    return False


def _proposed_value(question):
    for pattern in (r'是不是([\u3400-\u9fff]{1,8})', r'是否是([\u3400-\u9fff]{1,8})', r'是否为([\u3400-\u9fff]{1,8})', r'是([\u3400-\u9fff]{1,8})吗'):
        match=re.search(pattern, question)
        if not match:
            continue
        value=match.group(1)
        if value in PROPOSITION_STOP or any(value.startswith(word) for word in PROPOSITION_STOP):
            continue
        return value
    return None


def _variant_note(proposed, value):
    if proposed == value or len(proposed) != len(value):
        return ''
    pairs=[f'{a}/{b}' for a,b in zip(value,proposed) if a!=b]
    return f'命题「{proposed}」与著录「{value}」为字形异写（{"、".join(pairs)}），按同一取值判断。' if pairs else ''


def _history_document(stele_id):
    key=resolve_id(stele_id).get('historyKey')
    path=BASE/'data/history'/f'{key}.json' if key else None
    return (key, json.loads(path.read_text(encoding='utf-8'))) if path and path.is_file() else (None, None)


def _known(value):
    text=str(value or '').strip()
    return bool(text) and not text.startswith(UNKNOWN_PREFIXES)


def _comparable(value):
    return re.sub(r'[（(]拓本[)）]|\s', '', fold(value))


def cross_source_conflict(record, stele_id, facet_name, field):
    """Compare one catalogue field with the curated history document. Never picks a side."""
    if field not in CROSS_SOURCE_FIELDS:
        return None
    key, doc = _history_document(stele_id)
    if not doc:
        return None
    catalogue_value=_catalogue_value(record, field) if field+'Verification' in record else _verified_fact(record.get(field))
    history_value=doc.get(CROSS_SOURCE_FIELDS[field])
    if not _known(history_value):
        return None
    if catalogue_value is not None and _comparable(catalogue_value)==_comparable(history_value):
        return None
    sources=json.loads((BASE/'data/history/sources.json').read_text('utf8'))
    urls=[s['url'] for s in sources if s['id'] in doc.get('sourceIds',[]) and str(s.get('url','')).startswith('http')]
    shown_catalogue=catalogue_value or str(record.get(field) or '未核定')
    items=[
        {'source':'馆藏目录 catalog:'+stele_id,'url':record.get('sourceUrl'),'location':'data/catalog/steles28.json#'+stele_id,
         'quote':f'{facet_name}：{shown_catalogue}','status':'catalogue_record'},
        {'source':f'史料图谱 history:{key}','url':urls[0] if urls else None,'urls':urls,'location':f'data/history/{key}.json#{CROSS_SOURCE_FIELDS[field]}',
         'quote':f'{facet_name}：{history_value}','status':'curated_source_summary'},
    ]
    answer=(f'《{record["title"]}》的{facet_name}在不同资料中不一致，系统不选边，原样列出：'
            f'① 馆藏目录 catalog:{stele_id}：「{shown_catalogue}」；② 史料图谱 data/history/{key}.json：「{history_value}」。'
            '需人工复核后再统一著录。')
    return {'judgment':'conflict','basis':'cross_source_conflict','facet':facet_name,'proposed':None,'recorded':None,
            'steleId':stele_id,'sourceId':'catalog:'+stele_id,'sources':items,'forceRefusal':True,'answer':answer}


def _matched_facets(question):
    found=[]
    for name, field, keys in FACETS:
        if any(key in question for key in keys):
            found.append((name, field))
    return found


def _unverified_answer(record, facet, proposed):
    name, field = facet
    status = record.get(field + 'Verification') if field else None
    if status == 'pending_review':
        return f'《{record["title"]}》的{name}有待复核记录，本轮未升为已核定，不能判断命题「{proposed}」成立。'
    if status == 'disputed':
        return f'《{record["title"]}》的{name}存在著录争议，不能把命题「{proposed}」判成已核定。'
    return f'现有著录没有核定《{record["title"]}》的{name}，不能判断命题「{proposed}」是否成立。'


def _field_sources(stele_id, field):
    path = BASE / 'data/catalog/authorship-verification' / f'{stele_id}.json'
    if not field or not path.is_file():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    wanted = {field, {'author': 'inscriptionAuthor'}.get(field, field)}
    sources = []
    for item in data.get('evidence') or []:
        if item.get('field') not in wanted:
            continue
        sources.append({
            'source': item.get('source'),
            'url': item.get('sourceUrl'),
            'location': item.get('location'),
            'quote': item.get('quote'),
            'status': item.get('verificationStatus'),
        })
    return sources


def _dispute_claim(record, stele_id, source_id, facet_name, field, proposed):
    sources = _field_sources(stele_id, field)
    quotes = '；'.join(
        f'{item.get("source") or "来源"}：「{item.get("quote")}」' for item in sources if item.get('quote')
    )
    answer = f'《{record["title"]}》的{facet_name}存在著录争议。来源排序不能把另一条著录判成错误。'
    if quotes:
        answer += quotes + '。'
    if proposed:
        answer += f'命题「{proposed}」保持争议，不是已核定。'
    return {
        'judgment': 'disputed', 'basis': 'catalogue_conflict', 'facet': facet_name,
        'proposed': proposed, 'recorded': None, 'steleId': stele_id, 'sourceId': source_id,
        'sources': sources, 'forceRefusal': True, 'answer': answer,
    }


def judge_claim(question, work_ids):
    """Decide a catalogue-backed claim. Never fills a missing fact from model memory."""
    folded=fold(question)
    facets=_matched_facets(folded)
    if not facets:
        return None
    proposed=_proposed_value(question) or _proposed_value(folded)
    asking=any(word in folded for word in ASKING_WORDS) or proposed is not None
    if not asking:
        return None
    unsupported=[name for name, _field in facets if name in UNSUPPORTED_FACETS]
    if unsupported:
        return {'judgment':'insufficient_evidence','basis':'unsupported_facet','facet':unsupported[0],'proposed':proposed,'recorded':None,
                'steleId':None,'sourceId':None,'forceRefusal':True,
                'answer':f'「{unsupported[0]}」类问题当前不在检索判断范围内（著录核定状态不一，且未与志文逐条核对），不支持作答，也不作推断。'}
    catalog={record['id']: record for record in load('steles28.json')}
    unique=[]
    for stele_id in work_ids:
        canonical=canonical_id(stele_id)
        if canonical in catalog and canonical not in unique:
            unique.append(canonical)
    if len(unique)!=1:
        return {'judgment':'insufficient_evidence','basis':'insufficient_catalogue','facet':facets[0][0],'proposed':proposed,'recorded':None,
                'steleId':None,'sourceId':None,'forceRefusal':True,
                'answer':'问题没有唯一对应的已著录碑刻，不能合并不同文物作判断。'}
    stele_id=unique[0]
    record=catalog[stele_id]
    source_id='catalog:'+stele_id
    for name, field in facets:
        conflict=cross_source_conflict(record, stele_id, name, field)
        if conflict:
            if proposed:
                conflict['proposed']=proposed
                conflict['answer']+=f'命题「{proposed}」无法判断。'
            return conflict
    recorded={}
    missing=[]
    for name, field in facets:
        value=_catalogue_value(record, field) if field else None
        if value is None:
            missing.append((name, field))
        else:
            recorded[name]=value
    dispute = next(((name, field) for name, field in missing if field and record.get(field + 'Verification') == 'disputed'), None)
    if dispute and not recorded:
        return _dispute_claim(record, stele_id, source_id, dispute[0], dispute[1], proposed)
    if proposed is not None:
        if len(facets)!=1 or facets[0][0] in {item[0] for item in missing}:
            facet=facets[0][0]
            return {'judgment':'insufficient_evidence','basis':'insufficient_catalogue','facet':facet,'proposed':proposed,'recorded':None,
                    'steleId':stele_id,'sourceId':source_id,'forceRefusal':True,
                    'answer':_unverified_answer(record, facets[0], proposed)}
        facet, value=next(iter(recorded.items()))
        if _same_recorded_value(proposed, value):
            note=_variant_note(proposed, value)
            return {'judgment':'supported','basis':'catalogue_field_match_variant' if note else 'catalogue_field_match','facet':facet,'proposed':proposed,'recorded':value,
                    'steleId':stele_id,'sourceId':source_id,'forceRefusal':False,
                    'answer':f'判断：supported。著录{facet}为「{value}」，与命题的字段{"一致" if note else "完全一致"}。{note}依据 {source_id}。这只表示著录字段相符，不是独立史学鉴定。'}
        return {'judgment':'contradicted','basis':'catalogue_field_mismatch','facet':facet,'proposed':proposed,'recorded':value,
                'steleId':stele_id,'sourceId':source_id,'forceRefusal':False,
                'answer':f'判断：contradicted。著录字段为「{value}」，与命题「{proposed}」不一致。依据 {source_id}。这是著录字段不一致，不是独立史料反证。'}
    if missing and not recorded:
        names='、'.join(name for name, _field in missing)
        return {'judgment':'insufficient_evidence','basis':'insufficient_catalogue','facet':missing[0][0],'proposed':None,'recorded':None,
                'steleId':stele_id,'sourceId':source_id,'forceRefusal':True,
                'answer':f'《{record["title"]}》的{names}在现有著录中为未核定，不能补写。'}
    if missing:
        return {'judgment':'insufficient_evidence','basis':'insufficient_catalogue','facet':missing[0][0],'proposed':None,
                'recorded':recorded,'steleId':stele_id,'sourceId':source_id,'forceRefusal':True,
                'answer':'判断：insufficient_evidence。'+ '；'.join(f'{name}：{value}' for name,value in recorded.items()) + '。其余问项未核定，不能补写。'}
    summary='；'.join(f'{name}：{value}' for name,value in recorded.items())
    return {'judgment':'supported','basis':'catalogue_field_match','facet':'、'.join(recorded),'proposed':None,'recorded':recorded,
            'steleId':stele_id,'sourceId':source_id,'forceRefusal':False,
            'answer':f'判断：supported。著录{summary}。依据 {source_id}。'}


def demo_opt_in(question,stele_id=None,include_demo=False):
    """C-16: synthetic demo samples join retrieval only on explicit selection.

    Explicit means include_demo=True, a demo-sample scope id (legacy id or rm:demo:<id>),
    or an rm:demo: id written in the question. Words such as 样本/演示 alone do not opt in.
    """
    if include_demo:
        return 'include_demo'
    if stele_id and resolve_id(stele_id)['kind']=='demo_sample':
        return 'demo_scope_id'
    if 'rm:demo:' in (question or ''):
        return 'rm_demo_id_in_question'
    return None


def query(question,stele_id=None,limit=12,include_demo=False):
    ensure_index()
    normalized=canonical_id(stele_id)
    opt_in=demo_opt_in(question,stele_id,include_demo)
    with closing(sqlite3.connect(INDEX)) as conn:
        conn.row_factory=sqlite3.Row
        graph=json.loads(conn.execute("SELECT value FROM metadata WHERE key='graph'").fetchone()[0])
        all_records={r['source_id']:json.loads(r['record_json']) for r in conn.execute('SELECT * FROM evidence')}
        synthetic_ids=sorted({r['steleId'] for r in all_records.values() if (r.get('textProvenance') or {}).get('kind')=='synthetic_test_text'})
        if not opt_in:
            # Default retrieval never sees synthetic samples: drop their records, nodes, edges and places up front.
            hidden=set(synthetic_ids)
            all_records={k:v for k,v in all_records.items() if v['steleId'] not in hidden}
            hidden_nodes={n['id'] for n in graph['nodes'] if n['steleId'] in hidden}
            graph={'nodes':[n for n in graph['nodes'] if n['steleId'] not in hidden],
                   'edges':[e for e in graph['edges'] if e['source'] not in hidden_nodes and e['target'] not in hidden_nodes],
                   'places':[p for p in graph['places'] if p['steleId'] not in hidden]}
        # Resolve named entities before one-hop graph expansion; never merge identities by year.
        folded=fold(question)
        named_works=[n for n in graph['nodes'] if n['category'] in ('work','stele') and len(n['name'])>=2 and fold(n['name']) in folded]
        work_nodes={n['id']:n for n in graph['nodes'] if n['category']=='work'}
        alias_hits=[a for a in _work_aliases() if fold(a['alias']) in folded and a['steleId'] in work_nodes]
        for hit in alias_hits:
            if not any(n['steleId']==hit['steleId'] for n in named_works):
                named_works.append(work_nodes[hit['steleId']])
        scope_mismatch=bool(normalized and named_works and not any(n['steleId']==normalized for n in named_works))
        matched=[n for n in graph['nodes'] if len(n['name'])>=2 and fold(n['name']) in folded and (not normalized or n['steleId']==normalized)]
        matched.extend(n for n in named_works if n not in matched and (not normalized or n['steleId']==normalized))
        if opt_in and '建义' in question and ('样本' in question or '演示' in question) and (not normalized or normalized=='wei-jianyi'):
            matched.extend(n for n in graph['nodes'] if n['steleId']=='wei-jianyi')
        entity_ids={n['id'] for n in matched};artifact_ids={n['steleId'] for n in matched}
        if normalized:artifact_ids.add(normalized)
        terms=list(dict.fromkeys(tokens(question)+tokens(folded)))[:100]
        expression=' OR '.join('"'+t.replace('"','')+'"' for t in terms)
        hits=conn.execute('SELECT source_id,bm25(evidence_fts) AS rank FROM evidence_fts WHERE evidence_fts MATCH ? ORDER BY rank LIMIT 150',(expression,)).fetchall() if terms else []
        scores={r['source_id']:-float(r['rank']) for r in hits}
        bm25_only=dict(scores);boosted=set()
        expanded=[e for e in graph['edges'] if (e['source'] in entity_ids or e['target'] in entity_ids)]
        for n in matched:
            for sid in n['sourceIds']:scores[sid]=scores.get(sid,0)+10;boosted.add(sid)
        for edge in expanded:
            for sid in edge['sourceIds']:scores[sid]=scores.get(sid,0)+8;boosted.add(sid)
        if artifact_ids:
            scores={sid:score+3 for sid,score in scores.items() if sid in all_records and all_records[sid]['steleId'] in artifact_ids}
            boosted|=set(scores)
        ranked=sorted(scores,key=lambda sid:-scores[sid])
        candidates=[dict(all_records[sid],retrievalScore=scores[sid],bm25Score=bm25_only.get(sid,0.0),entityMatched=sid in boosted) for sid in ranked if sid in all_records]
        # Relevance threshold (calibrated on the 25 audit probes + 15 unrelated queries, see CONTENT_CHANGELOG):
        # entries with no entity/graph/scope match and BM25 below the threshold are not returned;
        # keyword-only entries at or above it are labelled weak.
        weak_dropped=[c for c in candidates if not c['entityMatched'] and c['bm25Score']<WEAK_BM25_THRESHOLD]
        evidence=[]
        for c in candidates:
            if c in weak_dropped:continue
            c['relevance']='entity_matched' if c['entityMatched'] else 'weak_keyword'
            if not c['entityMatched']:c['relevanceLabel']=WEAK_LABEL
            evidence.append(c)
        evidence=evidence[:limit]
        # No model fills unknown facts: unfamiliar questions return evidence only / insufficient.
        specific=bool(matched) or bool(normalized)
        supported_facets=tuple(dict.fromkeys([key for _name,_field,keys in FACETS for key in keys]+
            ['作者','年代','原刻','拓本','关系','原石','地点','身份','来源','馆藏','收藏','人物','纪年']))
        recognized=any(word in folded for word in supported_facets)
        status='evidence_found' if specific and evidence and recognized and not scope_mismatch else 'insufficient_evidence'
        if scope_mismatch:evidence=[];expanded=[]
        excerpts='\n'.join(f"[{i+1}] {r['text']}" for i,r in enumerate(evidence[:4]))
        if status=='evidence_found':
            answer='以下为现有资料原文/著录摘录，未调用语言模型：\n'+excerpts
        else:answer='现有资料不足以回答该问题。'+(('以下为相关检索条目，不构成问题结论。' if any(e['entityMatched'] for e in evidence) else '以下条目仅关键词命中，'+WEAK_LABEL+'。') if evidence else '')
        work_ids=[n['steleId'] for n in named_works if not normalized or n['steleId']==normalized]
        if normalized and not work_ids:
            work_ids=[normalized]
        claim=None if scope_mismatch else judge_claim(question, work_ids)
        judgment=claim['judgment'] if claim else ('insufficient_evidence' if status=='insufficient_evidence' else None)
        if claim and claim.get('judgment')=='disputed':
            status='disputed'
            answer=claim['answer']+' 未调用语言模型，不把争议字段改写成已核定。'
        elif claim and claim.get('judgment')=='conflict':
            status='conflict'
            answer=claim['answer']+' 未调用语言模型，不在冲突来源之间选边。'
        elif claim and claim.get('forceRefusal'):
            status='insufficient_evidence'
            answer=claim['answer']+' 未调用语言模型，不补写未核定史实。'
        elif claim:
            # A catalogue-backed judgment decides the status (C-04): never "insufficient" + "supported".
            if claim['sourceId'] in all_records and not any(r['sourceId']==claim['sourceId'] for r in evidence):
                evidence=[dict(all_records[claim['sourceId']],retrievalScore=scores.get(claim['sourceId'],0),bm25Score=bm25_only.get(claim['sourceId'],0.0),entityMatched=True,relevance='catalogue_claim')]+evidence[:limit-1]
            status='evidence_found'
            excerpts='\n'.join(f"[{i+1}] {r['text']}" for i,r in enumerate(evidence[:4]))
            answer=claim['answer']+'\n以下为现有资料原文/著录摘录，未调用语言模型：\n'+excerpts
        assert not (status=='insufficient_evidence' and judgment in ('supported','contradicted'))
        synthetic=[r['textProvenance']['label'] for r in evidence if (r.get('textProvenance') or {}).get('kind')=='synthetic_test_text']
        if synthetic:
            answer='注意：检索结果含'+synthetic[0]+'，不能作为史料证据。\n'+answer
        expanded_ids=entity_ids|{n for e in expanded for n in (e['source'],e['target'])}
        resolution=resolve_id(stele_id) if stele_id else None
        return {'query':question,'scopeSteleId':normalized,'scopeResolution':resolution,'status':status,'judgment':judgment,'claim':claim,
            'answer':answer,'answerMode':'extractive_evidence_only',
            'algorithmVersion':VERSION,'indexFingerprint':fingerprint(),'evidence':evidence,
            'entities':[n for n in graph['nodes'] if n['id'] in expanded_ids],'relations':expanded,'places':[p for p in graph['places'] if p['steleId'] in artifact_ids] if not scope_mismatch else [],
            'contentWarnings':sorted(set(synthetic)),'generation':None,
            'relevanceFilter':{'weakBm25Threshold':WEAK_BM25_THRESHOLD,'droppedBelowThreshold':len(weak_dropped),'weakLabel':WEAK_LABEL,
                               'rule':'未匹配实体/图谱/范围且 BM25 低于阈值的条目不返回；仅关键词命中且达到阈值的条目标“'+WEAK_LABEL+'”'},
            'demoScope':{'included':bool(opt_in),'optIn':opt_in,'syntheticSamples':synthetic_ids,
                         'note':'合成测试样本默认不参加检索；需 include_demo=true、演示样本 ID（如 rm:demo:wei-jianyi）作为范围，或在问题中写 rm:demo: ID'},'limitations':'BM25与实体一跳扩展；命题只对照已著录字段，未核定则拒答。摘记可能不完整，来源可追溯不表示链接实时可用。'}


def artifact_graph(stele_id):
    records,nodes,edges,places=corpus();canonical=canonical_id(stele_id)
    selected=[n for n in nodes if n['steleId']==canonical];ids={n['id'] for n in selected}
    return {'steleId':stele_id,'nodes':selected,'links':[e for e in edges if e['source'] in ids and e['target'] in ids],
            'sources':[r for r in records if r['steleId']==canonical and ':transcript:' not in r['sourceId']],
            'places':[p for p in places if p['steleId']==canonical],'routes':[],
            'verification':'来源支持的目录与史料关系，非新增历史推断；没有证据时不生成坐标或路线。'}
