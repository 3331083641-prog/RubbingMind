"""Red-team gate (7c0e258) non-blocking item: maintenance scripts follow RUBBINGMIND_* overrides
(defaults unchanged) instead of always writing the repository's own data/ and static/results."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migrate_state_paths_default_and_override(tmp_path, monkeypatch):
    migrate = _load('migrate_museum_v3')
    for name in ('RUBBINGMIND_DB_PATH', 'RUBBINGMIND_RUNTIME_DIR'):
        monkeypatch.delenv(name, raising=False)
    assert migrate.state_paths() == (ROOT / 'data' / 'rubbingmind.sqlite', ROOT / 'data' / 'runtime')
    monkeypatch.setenv('RUBBINGMIND_DB_PATH', str(tmp_path / 'copy.sqlite'))
    monkeypatch.setenv('RUBBINGMIND_RUNTIME_DIR', str(tmp_path / 'runtime'))
    assert migrate.state_paths() == ((tmp_path / 'copy.sqlite').resolve(), (tmp_path / 'runtime').resolve())
    # an explicit base (as the existing tests use) stays self-contained even with overrides set
    assert migrate.state_paths(tmp_path / 'b') == (tmp_path / 'b/data/rubbingmind.sqlite', tmp_path / 'b/data/runtime')


def test_assess_results_root_default_and_override(tmp_path, monkeypatch):
    assess = _load('assess_museum_condition')
    monkeypatch.delenv('RUBBINGMIND_RESULTS_DIR', raising=False)
    assert assess.results_root() == ROOT / 'static/results'
    monkeypatch.setenv('RUBBINGMIND_RESULTS_DIR', str(tmp_path / 'results'))
    assert assess.results_root() == (tmp_path / 'results').resolve()
