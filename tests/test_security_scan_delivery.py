"""Delivery scans respect Git exclusions and never disclose matched credentials."""
import subprocess

from scripts.security_scan import scan_repository


def _repo(tmp_path):
    subprocess.run(['git', 'init', str(tmp_path)], check=True, capture_output=True)
    (tmp_path/'.gitignore').write_text('.env\nwt/\n', encoding='utf-8')
    return 'sk-' + 'X' * 40  # fabricated scanner fixture, not a usable credential


def test_ignored_private_data_is_not_scanned_but_new_source_is(tmp_path, capsys):
    value=_repo(tmp_path)
    (tmp_path/'.env').write_text(value, encoding='utf-8')
    (tmp_path/'wt').mkdir()
    (tmp_path/'wt/private.py').write_text(value, encoding='utf-8')
    assert scan_repository(tmp_path)==0
    capsys.readouterr()
    (tmp_path/'new.py').write_text(value, encoding='utf-8')
    assert scan_repository(tmp_path)==1
    output=capsys.readouterr().out
    assert 'new.py' in output and value not in output and 'content redacted' in output


def test_environment_template_scanned_and_tracked_secret_file_rejected(tmp_path, capsys):
    value=_repo(tmp_path)
    (tmp_path/'.env.example').write_text(value, encoding='utf-8')
    assert scan_repository(tmp_path)==1
    assert value not in capsys.readouterr().out
    (tmp_path/'.env.example').write_text('# template only\n', encoding='utf-8')
    (tmp_path/'.env').write_text(value, encoding='utf-8')
    subprocess.run(['git','-C',str(tmp_path),'add','--force','.env'],check=True,capture_output=True)
    assert scan_repository(tmp_path)==1
    output=capsys.readouterr().out
    assert 'Credential file' in output and value not in output
