"""The shipped binary, not mocked geometry, must pass the PBR/UV audit in CI."""
from scripts.validate_stele_asset import run


def test_shipped_stele_has_valid_geometry_uvs_and_embedded_pbr():
    result=run()
    assert result['pass'] and result['external_image_uris']==0
    assert len(result['primitives'])==1
    assert len(result['embedded_images'])==4
    assert 0<result['triangles']<400000
