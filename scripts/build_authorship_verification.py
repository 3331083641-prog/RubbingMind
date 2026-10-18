"""Build per-stele authorship records from quotes already in the local catalogue.

A verified role must match a contiguous quote in the cited file. Catalogue names are
not upgraded from project notes, commentaries, or a shorter name inside a longer one.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / 'data/catalog/steles28.json'
OUT = ROOT / 'data/catalog/authorship-verification'
REVIEWED = '2026-10-18'

# quote, field, status, catalog name or None, note, location kind
# location kind: transcription | official | evidence
Claim = tuple


def role(name, status, note=''):
    return {'name': name, 'verificationStatus': status, 'note': note}


def claim(quote, field, status, catalog_name, note, kind, source_label):
    return {
        'quote': quote,
        'field': field,
        'verificationStatus': status,
        'catalogName': catalog_name,
        'note': note,
        'kind': kind,
        'sourceLabel': source_label,
    }


CLAIMS = {
    'han_01_caoquan': [
        claim('君諱全', 'steleSubject', 'verified', '曹全', '碑主，不是撰文或书丹。', 'transcription', '台北故宫博物院购拓000033释文'),
        claim('乃共刊石紀功', 'otherSignature', 'verified', None, '门下掾等刊石纪功，释文未给出书丹者姓名。', 'transcription', '台北故宫博物院购拓000033释文'),
    ],
    'han_02_yiying': [
        claim('魯前相瑛書言', 'steleSubject', 'pending_review', None, '释文见鲁前相瑛上书，未见独立撰文或书丹署名。', 'transcription', '台北故宫博物院释文'),
    ],
    'han_03_liqi': [
        claim('刊石表銘', 'otherSignature', 'verified', None, '刊石表铭，没有个人书丹署名。', 'transcription', '台北故宫博物院释文'),
    ],
    'wei_04_wangsong': [
        claim('輒憑以為銘', 'inscriptionAuthor', 'pending_review', None, '释文称抚军将军顿丘李奖撰铭，姓名在换行处分开，本轮不升为已核定撰文者。', 'transcription', '台北故宫博物院释文'),
    ],
    'tang_01_duobao': [
        claim('南陽岑勛撰', 'inscriptionAuthor', 'verified', '岑勋', '碑文署款。', 'transcription', '台北故宫博物院赠拓000365释文'),
        claim('琅邪顏真卿書', 'calligrapher', 'verified', '颜真卿', '碑文署款。', 'transcription', '台北故宫博物院赠拓000365释文'),
        claim('東海徐浩題額', 'titleCalligrapher', 'verified', '徐浩', '题额，不是撰文。', 'transcription', '台北故宫博物院赠拓000365释文'),
        claim('河南史華刻', 'engraver', 'verified', '史华', '刻工。', 'transcription', '台北故宫博物院赠拓000365释文'),
    ],
    'tang_02_jiucheng': [
        claim('臣魏徵奉', 'inscriptionAuthor', 'verified', '魏徵', '释文署奉撰；中间有空字符，不把空字符写入引文。', 'transcription', '台北故宫博物院释文'),
        claim('歐陽詢奉', 'calligrapher', 'verified', '欧阳询', '释文署奉书。', 'transcription', '台北故宫博物院释文'),
    ],
    'tang_03_yanjiamiao': [
        claim('顏真卿,Yan Zhenqing', 'calligrapher', 'verified', '颜真卿', '馆方作者栏。', 'official', '台北故宫博物院赠拓000305作者栏'),
        claim('唐顏真卿書顏氏家廟碑', 'calligrapher', 'verified', '颜真卿', '馆方作品名称。', 'official', '台北故宫博物院赠拓000305作品名称'),
        claim('真卿自撰正書', 'inscriptionAuthor', 'pending_review', None, '此句在题跋中，紧接按语，不是碑面独立署款。', 'official', '台北故宫博物院赠拓000305题跋'),
        claim('李陽冰篆額', 'titleCalligrapher', 'pending_review', None, '与自撰句同在题跋，不升为已核定篆额。', 'official', '台北故宫博物院赠拓000305题跋'),
    ],
    'tang_04_xuanmita': [
        claim('裴休撰', 'inscriptionAuthor', 'verified', '裴休', '碑文署款。', 'transcription', '台北故宫博物院释文'),
        claim('柳公權書', 'calligrapher', 'verified', '柳公权', '碑文署款。', 'transcription', '台北故宫博物院释文'),
        claim('并篆額', 'titleCalligrapher', 'verified', '柳公权', '同一署款写明书并篆额。', 'transcription', '台北故宫博物院释文'),
        claim('邵建和并弟建初鎸', 'engraver', 'verified', '邵建和、邵建初', '刻玉册官邵建和并弟建初。', 'transcription', '台北故宫博物院释文'),
    ],
    'song_01_yuanyou': [
        claim('元祐黨籍', 'otherSignature', 'verified', None, '释文仅录碑题并注明文不录，没有撰书署名。', 'transcription', '台北故宫博物院释文'),
    ],
    'song_02_wenxuan': [
        claim('宋太宗御製至聖文宣王贊碑', 'inscriptionAuthor', 'verified', '宋太宗', '馆方题名写明御制。御制是撰作，不是书丹。', 'transcription', '台北故宫博物院购拓000260题名与释文'),
        claim('玄聖文宣王贊并序。御製', 'inscriptionAuthor', 'verified', '宋太宗', '碑文自题御制，未署书丹人。', 'transcription', '台北故宫博物院购拓000260释文'),
    ],
    'song_03_daguan': [
        claim('李時雍奉勑摹寫', 'calligrapher', 'verified', '李时雍', '奉敕摹写御笔，是上石书写者，不是诏旨的原始执笔皇帝。', 'transcription', '台北故宫博物院释文'),
        claim('蔡京奉勑題額', 'titleCalligrapher', 'verified', '蔡京', '奉敕题额。', 'transcription', '台北故宫博物院释文'),
        claim('御筆八行詔旨', 'inscriptionAuthor', 'pending_review', None, '释文称为御笔，摘录未写出皇帝姓名，不补作宋徽宗。', 'transcription', '台北故宫博物院释文'),
    ],
    'song_04_mengying': [
        claim('南岳宣義大師夢英十八體書', 'calligrapher', 'verified', '释梦英', '碑题署梦英十八体书。', 'transcription', '台北故宫博物院释文'),
        claim('宋釋夢英十八體書碑', 'calligrapher', 'verified', '释梦英', '馆方题名。各体所录文字作者并非一人，撰文不据此补定。', 'official', '台北故宫博物院购拓000259作品名称'),
    ],
    'yuan_01_yufu': [
        claim('趙世延奉勅譔', 'inscriptionAuthor', 'verified', '赵世延', '奉敕撰，不是赵孟頫。', 'transcription', '台北故宫博物院释文'),
        claim('趙孟頫奉勅書', 'calligrapher', 'verified', '赵孟頫', '奉敕书。', 'transcription', '台北故宫博物院释文'),
        claim('李孟奉勅篆額', 'titleCalligrapher', 'verified', '李孟', '奉敕篆额。', 'transcription', '台北故宫博物院释文'),
    ],
    'yuan_02_sundeyu': [
        claim('趙文原譔', 'inscriptionAuthor', 'disputed', None, '馆方释文作赵文原。通行著录常作邓文原。未对照原石，两种写法都不升为已核定。', 'transcription', '台北故宫博物院释文'),
        claim('趙孟頫書', 'calligrapher', 'verified', '赵孟頫', '释文署书。', 'transcription', '台北故宫博物院释文'),
        claim('趙世延篆額', 'titleCalligrapher', 'verified', '赵世延', '释文署篆额。', 'transcription', '台北故宫博物院释文'),
    ],
    'yuan_03_shengzhu': [
        claim('王思廉撰', 'inscriptionAuthor', 'verified', '王思廉', '释文署撰。', 'transcription', '台北故宫博物院释文'),
        claim('趙孟頫書', 'calligrapher', 'verified', '赵孟頫', '释文署书。', 'transcription', '台北故宫博物院释文'),
        claim('（篆題）', 'titleCalligrapher', 'pending_review', None, '篆题二字在释文括号补字内，不升为已核定。', 'transcription', '台北故宫博物院释文'),
    ],
    'yuan_04_jingyuanchang': [
        claim('元赵孟頫书元故太常博士敬元长墓碣铭', 'calligrapher', 'pending_review', None, '证据包所存馆方题名写赵孟頫书。题名不是撰文署名。本轮未重开馆方页面。', 'evidence', '证据包 item_title，对应故宫赠拓000412'),
        claim('敬元长墓碣铭', 'steleSubject', 'pending_review', '敬元长', '题名中的墓主。书写者不因此成为撰文者。', 'evidence', '证据包 item_title，对应故宫赠拓000412'),
    ],
    'ming_02_luxianzhi': [
        claim('文徵明著', 'inscriptionAuthor', 'verified', '文徵明', '志文末署文徵明著。', 'transcription', '台北故宫博物院释文'),
        claim('明文徵明書陸獻之墓誌銘', 'calligrapher', 'verified', '文徵明', '馆方题名写明书。', 'transcription', '台北故宫博物院题名'),
        claim('陸獻之墓誌銘', 'steleSubject', 'verified', '陆献之', '题名与志题中的墓主，不是撰文者。', 'transcription', '台北故宫博物院题名'),
    ],
    'ming_03_wugou': [
        claim('無垢子', 'steleSubject', 'pending_review', None, '碑题作无垢子何君，何字在释文括号内，墓主姓名不升为已核定。', 'transcription', '台北故宫博物院释文'),
    ],
    'ming_04_tongdian': [
        claim('王毓宗頓首撰', 'inscriptionAuthor', 'verified', '王毓宗', '碑文末署。', 'transcription', '台北故宫博物院释文'),
        claim('王羲之書', 'calligrapher', 'disputed', None, '署款在换行后作王羲之书，碑年为1603，不能核定晋人王羲之为这块明碑的书丹者。', 'transcription', '台北故宫博物院释文'),
        claim('吳郡吳士瑞集', 'otherSignature', 'pending_review', None, '集字者，不是原书丹者。', 'transcription', '台北故宫博物院释文'),
        claim('雲中朱廷', 'engraver', 'pending_review', None, '刻工名下一字为缺字方框，不补全姓名。', 'transcription', '台北故宫博物院释文'),
    ],
    'qing_01_qianlong_heart_sutra': [
        claim('乾隆御书般若波罗蜜多心经', 'calligrapher', 'pending_review', None, '证据包题名作乾隆御书。心经正文不是乾隆所撰。本轮未重开普林斯顿页面。', 'evidence', '证据包 item_title，普林斯顿大学艺术博物馆 y1958-220'),
    ],
    'qing_03_sanxitang_preface': [
        claim('御序', 'inscriptionAuthor', 'pending_review', None, '目录已区分御序撰于1747年。对象是法帖御序刻石拓本，不是法帖所收原迹作者。馆方全文抽取为空。', 'catalog', 'data/catalog/steles28.json 原刻年代说明'),
    ],
}

CONFLICTS = {
    'tang_03_yanjiamiao': [{
        'field': 'inscriptionAuthor',
        'status': 'pending_review',
        'detail': '「真卿自撰正书。李阳冰篆额。」位于题跋，后面是「按真卿生于唐中宗景龙三年」。这不是碑面独立署款。',
    }],
    'yuan_02_sundeyu': [{
        'field': 'inscriptionAuthor',
        'status': 'disputed',
        'detail': '本馆释文连续文字是「赵文原譔」。孙德彧道行碑通常著录为邓文原撰、赵孟頫书、赵世延篆额。本轮不改字，也不把赵文原或邓文原写成已核定撰文者。',
    }],
    'yuan_03_shengzhu': [{
        'field': 'titleCalligrapher',
        'status': 'pending_review',
        'detail': '书丹「赵孟頫书」为释文原文。同句后的篆题在括号补字中。',
    }],
    'yuan_04_jingyuanchang': [{
        'field': 'inscriptionAuthor',
        'status': 'unknown',
        'detail': '赵孟頫书写墓碣铭，不因此成为撰文者。敬元长是墓主。',
    }],
    'ming_04_tongdian': [{
        'field': 'calligrapher',
        'status': 'disputed',
        'detail': '释文同时出现王毓宗撰、朱廷某镌、晋右军将军王羲之书、吴郡吴士瑞集。王羲之不能核定为1603年这块碑的书丹者。',
    }],
    'qing_01_qianlong_heart_sutra': [{
        'field': 'inscriptionAuthor',
        'status': 'unknown',
        'detail': '般若心经有独立的译经文本。乾隆御书只可能说明书写，不能把弘历登记为经文撰者。',
    }],
    'qing_02_wushi_reerection': [{
        'field': 'artifactIdentity',
        'status': 'pending_review',
        'detail': '这是清代重立石记，不是东汉武氏祠画像石。目录中的翁方纲未在空的馆方全文抽取里出现，项目加工说明不单独升为已核定。',
    }],
    'qing_03_sanxitang_preface': [{
        'field': 'artifactIdentity',
        'status': 'pending_review',
        'detail': '须区分三希堂法帖、乾隆御序和这块刻石拓本。御序书写者不等于法帖所收晋唐作品的书家。',
    }],
    'song_02_wenxuan': [{
        'field': 'calligrapher',
        'status': 'unknown',
        'detail': '御制说明诏文撰作来源。释文未署书丹人。',
    }],
    'song_03_daguan': [{
        'field': 'inscriptionAuthor',
        'status': 'pending_review',
        'detail': '正文称为御笔八行诏旨。摘录没有皇帝姓名，不补宋徽宗。李时雍是奉敕摹写者。',
    }],
}


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    path.write_bytes(text.replace('\n', '\r\n').encode('utf-8'))


def source_text(item, evidence, kind):
    if kind == 'transcription':
        return (item.get('transcription') or '').replace('\x00', '')
    if kind == 'official':
        return (evidence.get('officialExtractedText') or '').replace('\x00', '')
    if kind == 'evidence':
        return json.dumps(evidence, ensure_ascii=False).replace('\x00', '')
    if kind == 'catalog':
        return json.dumps(item, ensure_ascii=False)
    raise ValueError(kind)


def location_for(item, kind):
    evidence_file = item['sourceVerification']['evidenceFile']
    if kind == 'transcription':
        return f"data/catalog/steles28.json#{item['id']}.transcription"
    if kind == 'official':
        return evidence_file + '#officialExtractedText'
    if kind == 'evidence':
        return evidence_file
    if kind == 'catalog':
        return f"data/catalog/steles28.json#{item['id']}"
    raise ValueError(kind)


def blank(note):
    return role(None, 'unknown', note)


def pair_status(author, calligrapher):
    statuses = {author['verificationStatus'], calligrapher['verificationStatus']}
    if 'disputed' in statuses:
        return 'disputed'
    if 'pending_review' in statuses:
        return 'pending_review'
    if statuses == {'verified'}:
        return 'verified'
    if 'verified' in statuses:
        return 'partial'
    return 'unknown'


def main():
    items = load_json(CATALOG_PATH)
    by_id = {item['id']: item for item in items}
    OUT.mkdir(parents=True, exist_ok=True)
    catalog_updates = {}
    for item in items:
        evidence = load_json(ROOT / item['sourceVerification']['evidenceFile'])
        found = []
        for entry in CLAIMS.get(item['id'], []):
            text = source_text(item, evidence, entry['kind'])
            if entry['quote'] not in text:
                raise SystemExit(f"quote missing for {item['id']} {entry['field']}: {entry['quote']}")
            found.append({
                'field': entry['field'],
                'quote': entry['quote'],
                'verificationStatus': entry['verificationStatus'],
                'sourceLabel': entry['sourceLabel'],
                'sourceUrl': item['sourceUrl'],
                'accessionNumber': item['collectionNumber'],
                'location': location_for(item, entry['kind']),
                'note': entry['note'],
            })
            if entry['catalogName'] and entry['verificationStatus'] in ('verified', 'pending_review'):
                catalog_updates.setdefault(item['id'], {})[entry['field']] = (entry['catalogName'], entry['verificationStatus'])
        roles = {
            'inscriptionAuthor': blank('未见可核定的撰文署名。'),
            'calligrapher': blank('未见可核定的书丹署名。'),
            'titleCalligrapher': blank('未见可核定的篆额或题额署名。'),
            'engraver': blank('未见可核定的刻工署名。'),
            'steleSubject': blank('不把碑名中的通称自动写成墓主。'),
        }
        notes = []
        for entry in CLAIMS.get(item['id'], []):
            if entry['field'] not in roles:
                notes.append(entry['note'])
                continue
            current = roles[entry['field']]
            incoming = entry['verificationStatus']
            rank = {'unknown': 0, 'pending_review': 1, 'disputed': 3, 'verified': 2}
            if rank[incoming] >= rank[current['verificationStatus']]:
                name = entry['catalogName'] if incoming in ('verified', 'pending_review') else None
                roles[entry['field']] = role(name, incoming, entry['note'])
        if item['id'] not in CLAIMS:
            notes.append('本轮未在馆方释文或题名中找到可升级的署名；原目录中的未核定或既有姓名保持原状。')
        record = {
            'steleId': item['id'],
            'title': item['title'],
            'dynasty': item['dynasty'],
            'originalYear': item['originalYear'],
            'rubbingPeriod': item['rubbingPeriod'],
            'artifactType': item['artifactType'],
            'rubbingCollectionInstitution': item['rubbingCollectionInstitution'],
            'collectionNumber': item['collectionNumber'],
            'sourceUrl': item['sourceUrl'],
            'inscriptionAuthor': roles['inscriptionAuthor'],
            'calligrapher': roles['calligrapher'],
            'titleCalligrapher': roles['titleCalligrapher'],
            'engraver': roles['engraver'],
            'steleSubject': roles['steleSubject'],
            'verificationStatus': pair_status(roles['inscriptionAuthor'], roles['calligrapher']),
            'evidence': found,
            'conflicts': CONFLICTS.get(item['id'], []),
            'notes': notes,
            'reviewedAt': REVIEWED,
            'method': '只采用本地馆藏释文、馆方题名或证据包中的连续引文。未重开网页时不把目录旧值升为已核定。',
        }
        write_json(OUT / f"{item['id']}.json", record)
        for field, key in (
            ('inscriptionAuthor', 'author'),
            ('calligrapher', 'calligrapher'),
            ('titleCalligrapher', 'titleCalligrapher'),
            ('engraver', 'engraver'),
            ('steleSubject', 'steleSubject'),
        ):
            status = roles[field]['verificationStatus']
            current_name = item.get(key)
            if status == 'unknown' and current_name not in (None, '未核定'):
                status = 'pending_review'
            item[key + 'Verification'] = status
    for item in items:
        item.pop('inscriptionAuthor', None)
    catalog_key = {'inscriptionAuthor': 'author', 'calligrapher': 'calligrapher', 'titleCalligrapher': 'titleCalligrapher', 'engraver': 'engraver', 'steleSubject': 'steleSubject'}
    for stele_id, updates in catalog_updates.items():
        item = by_id[stele_id]
        item.pop('inscriptionAuthor', None)
        for field, (value, status) in updates.items():
            key = catalog_key[field]
            current = item.get(key)
            if status != 'verified' and current not in (None, '未核定', value):
                continue
            if current not in (None, '未核定', value):
                raise SystemExit(f'refuse overwrite {stele_id} {key}: {current} -> {value}')
            item[key] = value
    for item in items:
        for field in ('titleCalligrapher', 'engraver', 'steleSubject'):
            item.setdefault(field, '未核定')
    write_json(CATALOG_PATH, items)
    print(json.dumps({'records': len(items), 'updatedWorks': sorted(catalog_updates)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
