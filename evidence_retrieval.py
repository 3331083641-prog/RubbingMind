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
from history_graph import CORE_IDS, ALIASES

INDEX=BASE/'data/runtime/evidence-v2.sqlite'
VERSION='fts5-evidence-graph-v2.1'


def canonical_id(stele_id):
    return {v:k for k,v in ALIASES.items()}.get(stele_id,stele_id)


def tokens(text):
    chars=re.findall(r'[\u3400-\u9fff]|[a-zA-Z0-9_-]+',text.lower())
    return list(dict.fromkeys(chars+[a+b for a,b in zip(chars,chars[1:]) if len(a)==len(b)==1]))


def corpus():
    records=[];nodes=[];edges=[];places=[]
    def add(source_id,stele_id,title,text,url,institution,location,level='catalogue_record',license=None):
        records.append({'sourceId':source_id,'steleId':stele_id,'title':title,'text':text,'url':url,
            'institution':institution,'evidenceLevel':level,'originalPosition':location,'license':license,
            'origin':'reviewed_local_record','textSha256':hashlib.sha256(text.encode()).hexdigest()})
    for r in load('steles28.json'):
        sid=r['id'];eid='catalog:'+sid
        facts=f"{r['title']}。原刻朝代：{r['dynasty']}；原刻年代：{r['originalYear']}；拓本年代：{r['rubbingPeriod']}；文物类型：{r['artifactType']}；撰文：{r['author']}；书丹：{r['calligrapher']}；拓本现藏机构：{r['rubbingCollectionInstitution']}；拓本馆藏编号：{r['collectionNumber']}；原石现藏机构：{r.get('physicalCollectionInstitution') or '未核定'}；原碑所在地：{r.get('originalLocation') or '未核定'}。"
        add(eid,sid,r['title']+' · 馆藏著录',facts,r['sourceUrl'],r['rubbingCollectionInstitution'],'data/catalog/steles28.json#'+sid,license=r['license'])
        nodes.append({'id':sid,'name':r['title'],'category':'work','steleId':sid,'sourceIds':[eid]})
        # A work, its physical stone, and a particular collected rubbing are distinct.
        for key,name,category,relation in [('stone',r['title']+'原石','stone','原刻'),('rubbing',r['collectionNumber']+'拓本','rubbing','拓本见证'),
            ('year',r['originalYear'],'date','原刻纪年'),('collection',r['rubbingCollectionInstitution'],'institution','拓本现藏')]:
            target=sid+':'+key;nodes.append({'id':target,'name':name,'category':category,'steleId':sid,'sourceIds':[eid]})
            edges.append({'source':sid+':rubbing' if key=='collection' else sid,'target':target,'relation':relation,'sourceIds':[eid],'sourceUrl':r['sourceUrl']})
        for key,relation in [('author','撰文'),('calligrapher','书丹')]:
            if r[key] and r[key]!='未核定':
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
                'identity_unverified' if core_id=='wei-jianyi' else 'curated_source_summary')
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
                'identity_unverified' if core_id=='wei-jianyi' else 'sourced_relationship')
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
                conn.execute('INSERT INTO evidence_fts VALUES (?,?,?)',(r['sourceId'],' '.join(tokens(r['title'])),' '.join(tokens(r['text']))))
            for key,value in [('fingerprint',fingerprint()),('graph',json.dumps({'nodes':nodes,'edges':edges,'places':places},ensure_ascii=False))]:
                conn.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',(key,value))


def query(question,stele_id=None,limit=12):
    ensure_index()
    normalized=canonical_id(stele_id)
    with closing(sqlite3.connect(INDEX)) as conn:
        conn.row_factory=sqlite3.Row
        graph=json.loads(conn.execute("SELECT value FROM metadata WHERE key='graph'").fetchone()[0])
        all_records={r['source_id']:json.loads(r['record_json']) for r in conn.execute('SELECT * FROM evidence')}
        # Resolve named entities before one-hop graph expansion; never merge identities by year.
        named_works=[n for n in graph['nodes'] if n['category'] in ('work','stele') and len(n['name'])>=2 and n['name'] in question]
        scope_mismatch=bool(normalized and named_works and not any(n['steleId']==normalized for n in named_works))
        matched=[n for n in graph['nodes'] if len(n['name'])>=2 and n['name'] in question and (not normalized or n['steleId']==normalized)]
        if '建义' in question and ('样本' in question or '演示' in question) and (not normalized or normalized=='wei-jianyi'):
            matched.extend(n for n in graph['nodes'] if n['steleId']=='wei-jianyi')
        entity_ids={n['id'] for n in matched};artifact_ids={n['steleId'] for n in matched}
        if normalized:artifact_ids.add(normalized)
        terms=tokens(question)[:100]
        expression=' OR '.join('"'+t.replace('"','')+'"' for t in terms)
        hits=conn.execute('SELECT source_id,bm25(evidence_fts) AS rank FROM evidence_fts WHERE evidence_fts MATCH ? ORDER BY rank LIMIT 150',(expression,)).fetchall() if terms else []
        scores={r['source_id']:-float(r['rank']) for r in hits}
        expanded=[e for e in graph['edges'] if (e['source'] in entity_ids or e['target'] in entity_ids)]
        for n in matched:
            for sid in n['sourceIds']:scores[sid]=scores.get(sid,0)+10
        for edge in expanded:
            for sid in edge['sourceIds']:scores[sid]=scores.get(sid,0)+8
        if artifact_ids:
            scores={sid:score+3 for sid,score in scores.items() if sid in all_records and all_records[sid]['steleId'] in artifact_ids}
        ranked=sorted(scores,key=lambda sid:-scores[sid])
        evidence=[dict(all_records[sid],retrievalScore=scores[sid]) for sid in ranked[:limit] if sid in all_records]
        # No model fills unknown facts: unfamiliar questions return evidence only / insufficient.
        specific=bool(matched) or bool(normalized)
        supported_facets=('撰文','书丹','作者','年代','原刻','拓本','关系','原石','地点','身份','来源','馆藏','收藏','人物','纪年')
        recognized=any(word in question for word in supported_facets)
        status='evidence_found' if specific and evidence and recognized and not scope_mismatch else 'insufficient_evidence'
        if scope_mismatch:evidence=[];expanded=[]
        if status=='evidence_found':
            answer='以下为现有资料原文/著录摘录，未调用语言模型：\n'+'\n'.join(f"[{i+1}] {r['text']}" for i,r in enumerate(evidence[:4]))
        else:answer='现有资料不足以回答该问题。'+('以下为相关检索条目，不构成问题结论。' if evidence else '')
        expanded_ids=entity_ids|{n for e in expanded for n in (e['source'],e['target'])}
        return {'query':question,'scopeSteleId':normalized,'status':status,'answer':answer,'answerMode':'extractive_evidence_only',
            'algorithmVersion':VERSION,'indexFingerprint':fingerprint(),'evidence':evidence,
            'entities':[n for n in graph['nodes'] if n['id'] in expanded_ids],'relations':expanded,'places':[p for p in graph['places'] if p['steleId'] in artifact_ids] if not scope_mismatch else [],
            'generation':None,'limitations':'BM25与实体一跳扩展；摘记可能不完整，未进行语义蕴含或独立史学鉴定。来源可追溯不表示链接实时可用。'}


def artifact_graph(stele_id):
    records,nodes,edges,places=corpus();canonical=canonical_id(stele_id)
    selected=[n for n in nodes if n['steleId']==canonical];ids={n['id'] for n in selected}
    return {'steleId':stele_id,'nodes':selected,'links':[e for e in edges if e['source'] in ids and e['target'] in ids],
            'sources':[r for r in records if r['steleId']==canonical and ':transcript:' not in r['sourceId']],
            'places':[p for p in places if p['steleId']==canonical],'routes':[],
            'verification':'来源支持的目录与史料关系，非新增历史推断；没有证据时不生成坐标或路线。'}
