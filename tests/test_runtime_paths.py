"""R1-7: RUBBINGMIND_* path overrides; defaults must equal the historical locations."""
import json
import os
import subprocess
import sys
from pathlib import Path

import runtime_paths

ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
import json, database, upload_storage, glyph_inference, glyph_annotations, catalog_assessment, evidence_retrieval, museum_processing
print(json.dumps({"db": database.DB_PATH, "upload": str(upload_storage.UPLOAD_DIR), "infer": str(glyph_inference.INFERENCE_DIR),
  "ann": str(glyph_annotations.RUNTIME_DIR), "reviews": str(catalog_assessment.REVIEWS), "index": str(evidence_retrieval.INDEX),
  "results": str(museum_processing.results_root())}))
'''


def _probe(extra_env):
    env = {k: v for k, v in os.environ.items() if k not in runtime_paths.ENV_VARS}
    env.update(extra_env, PYTHONIOENCODING='utf-8')
    out = subprocess.run([sys.executable, '-c', PROBE], cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_defaults_are_historical_locations():
    got = _probe({})
    assert Path(got['db']) == ROOT / 'data' / 'rubbingmind.sqlite'
    assert Path(got['upload']) == ROOT / 'data' / 'uploads'
    assert Path(got['infer']) == ROOT / 'data' / 'runtime' / 'glyph-inferences'
    assert Path(got['ann']) == ROOT / 'data' / 'runtime' / 'glyph-annotations'
    assert Path(got['reviews']) == ROOT / 'data' / 'runtime' / 'condition-reviews'
    assert Path(got['index']) == ROOT / 'data' / 'runtime' / 'evidence-v2.sqlite'
    assert Path(got['results']) == ROOT / 'static' / 'results'


def test_overrides_relocate_all_mutable_state(tmp_path):
    got = _probe({
        'RUBBINGMIND_DB_PATH': str(tmp_path / 'db' / 'copy.sqlite'),
        'RUBBINGMIND_RUNTIME_DIR': str(tmp_path / 'runtime'),
        'RUBBINGMIND_UPLOAD_DIR': str(tmp_path / 'uploads'),
        'RUBBINGMIND_RESULTS_DIR': str(tmp_path / 'results'),
    })
    tmp = tmp_path.resolve()
    assert Path(got['db']) == tmp / 'db' / 'copy.sqlite'
    assert Path(got['upload']) == tmp / 'uploads'
    for key, name in [('infer', 'glyph-inferences'), ('ann', 'glyph-annotations'), ('reviews', 'condition-reviews'), ('index', 'evidence-v2.sqlite')]:
        assert Path(got[key]) == tmp / 'runtime' / name
    assert Path(got['results']) == tmp / 'results'
    for value in got.values():
        assert not Path(value).is_relative_to(ROOT)


def test_relocated_results_served_under_unchanged_url(tmp_path):
    (tmp_path / 'results' / 'probe' / 'r').mkdir(parents=True)
    (tmp_path / 'results' / 'probe' / 'r' / 'x.txt').write_text('relocated', 'utf-8')
    code = r'''
from fastapi.testclient import TestClient
import main
r = TestClient(main.app).get("/static/results/probe/r/x.txt")
print(r.status_code, r.text)
'''
    env = {k: v for k, v in os.environ.items() if k not in runtime_paths.ENV_VARS}
    env.update(RUBBINGMIND_RESULTS_DIR=str(tmp_path / 'results'), RUBBINGMIND_DB_PATH=str(tmp_path / 'db.sqlite'),
               RUBBINGMIND_RUNTIME_DIR=str(tmp_path / 'runtime'), RUBBINGMIND_UPLOAD_DIR=str(tmp_path / 'uploads'),
               PYTHONIOENCODING='utf-8')
    out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    assert out.stdout.strip().splitlines()[-1] == '200 relocated'


def test_empty_variable_means_default(monkeypatch):
    monkeypatch.setenv('RUBBINGMIND_DB_PATH', '  ')
    assert Path(runtime_paths.db_path()) == ROOT / 'data' / 'rubbingmind.sqlite'
