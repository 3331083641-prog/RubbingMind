import numpy as np

from degradation_analysis import VERSION, interior_constant_block
from experiments.synthetic_v22 import run


def test_v22_candidate_refuses_exact_flat_occlusion_without_replacing_v21():
    assert VERSION == 'adaptive-rubbing-v2.1'
    report = run()
    assert report['productionVersion'] == 'adaptive-rubbing-v2.1'
    rows = {(row['method'], row['degradation']): row for row in report['rows']}
    occlusion = rows[('adaptive_v22_candidate', 'occlusion')]
    assert occlusion['unchanged'] is True
    assert occlusion['negativeLift'] is False
    assert 'skip_flat_interior' in occlusion['operators']
    gaussian = rows[('adaptive_v22_candidate', 'gaussian')]
    assert gaussian['unchanged'] is False
    assert 'skip_flat_interior' not in gaussian['operators']
    blank = np.full((64, 64), 200, np.uint8)
    assert interior_constant_block(blank) is True
    noisy = blank.copy()
    noisy[8:-8, 8:-8] = np.arange(48 * 48, dtype=np.uint8).reshape(48, 48)
    assert interior_constant_block(noisy) is False
