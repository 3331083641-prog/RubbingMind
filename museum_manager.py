"""Reviewed catalogue facade: no startup database rewriting."""
from collections import Counter
from catalog import BASE,load,museum_records
import json
from upload_storage import get_upload, list_uploads
class MuseumManager:
    def __init__(self):
        self.steles=museum_records();self.cores=load('core_samples.json')
        self.retired={r['oldId']:r for r in load('replacement_mapping.json')};self.aliases=load('review_aliases.json')
    def get_all_steles(self):return self.steles+list_uploads()
    def get_stele_by_id(self,stele_id):
        if stele_id.startswith('upload-'):
            return get_upload(stele_id)
        target=self.aliases.get(stele_id,stele_id)
        for r in self.steles+self.cores:
            if r['id']==target:return r
        path=BASE/'data/museum_database.json'
        if path.exists() and stele_id not in self.retired:
            for r in json.loads(path.read_text('utf-8')):
                if r['id']==stele_id and r.get('source_kind')!='verified_review_v3':return r
        return None
    def refresh_images_status(self):
        return sum((BASE/'apps/web/public'/r['imageAssets']['cover'].split('?')[0].lstrip('/')).exists() for r in self.steles)
    def get_dynasty_counts(self):return dict(all=len(self.steles),**Counter(r['dynasty_value'] for r in self.steles))
museum_manager=MuseumManager()
