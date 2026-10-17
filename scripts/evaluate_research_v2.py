import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_retrieval import query


def main():
    config=json.loads((ROOT/'data/catalog/research-evaluation-v2.json').read_text('utf8'));cases=[]
    for case in config['cases']:
        result=query(case['question']);text=result['answer']+' '.join(e['text'] for e in result['evidence'])
        assertions={term:term in text for term in case['expectedTerms']}
        if case.get('expectedEvidenceId'):assertions['expectedEvidenceHit']=case['expectedEvidenceId'] in {e['sourceId'] for e in result['evidence']}
        if case.get('expectedStatus'):assertions['status']=result['status']==case['expectedStatus']
        cases.append({'id':case['id'],'assertions':assertions,'passed':all(assertions.values()),'actual':result})
    report={'basis':config['annotationBasis'],'allAssertionsPass':all(c['passed'] for c in cases),'cases':cases}
    path=ROOT/'docs/audit/technical-v2-research-evaluation.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print([(r['id'],r['passed']) for r in cases]);assert report['allAssertionsPass']


if __name__=='__main__':main()
