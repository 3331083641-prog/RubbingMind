import hashlib
import inspect
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from algorithm_engine import algorithm_engine, base64_to_mat
from degradation_analysis import AdaptiveRubbingRestorer, analyze_degradation, preserve_missing_regions
from main import app


def test_input_only_decisions_and_periodic_evidence():
    assert 'reference' not in inspect.signature(AdaptiveRubbingRestorer.restore).parameters
    assert 'degradation' not in inspect.signature(AdaptiveRubbingRestorer.restore).parameters
    y,x=np.mgrid[:256,:256]
    clean=np.full((256,256),80,np.uint8);clean[70:190,100:130]=190
    untouched, details=AdaptiveRubbingRestorer().restore(clean)
    assert np.array_equal(untouched,clean)
    assert not details['features']['periodicPeaks']
    periodic=np.clip(clean.astype(float)+25*np.sin(2*np.pi*x/8),0,255).astype(np.uint8)
    output, details=AdaptiveRubbingRestorer().restore(periodic)
    assert details['features']['periodicPeaks']
    assert any(d['operator']=='notch' for d in details['decisions'])
    assert np.mean((output.astype(float)-clean)**2)<np.mean((periodic.astype(float)-clean)**2)


def test_noise_strength_and_gate_do_not_claim_truth():
    rng=np.random.default_rng(15)
    clean=np.full((128,128),90,np.uint8);clean[30:90,55:65]=210
    noise=np.clip(clean.astype(float)+rng.normal(0,14,clean.shape),0,255).astype(np.uint8)
    a,details=AdaptiveRubbingRestorer().restore(noise,strength=.6)
    b,_=AdaptiveRubbingRestorer().restore(noise,strength=1.3)
    assert not np.array_equal(a,b)
    assert 'psnr' not in str(details).lower()
    assert details['fidelityGate']['basis'].startswith('输入输出')


def test_full_skeleton_thick_strokes_and_separate_contour():
    image=np.zeros((140,140),np.uint8);image[20:120,30:110]=255
    skeleton=algorithm_engine.extract_stroke_skeleton(image)
    assert 0 < np.count_nonzero(skeleton) < 150
    assert cv2.connectedComponents(skeleton)[0] == 2
    assert skeleton[70,70]>0 or skeleton[69,69]>0


def test_seeded_art_and_weathering_are_reproducible():
    img=np.full((64,64),80,np.uint8);img[20:45,30:36]=180
    mask=np.zeros_like(img);mask[10:20,10:20]=255
    a=algorithm_engine.process_rubbing(img,damage_mask=mask,random_seed=17)
    b=algorithm_engine.process_rubbing(img,damage_mask=mask,random_seed=17)
    c=algorithm_engine.process_rubbing(img,damage_mask=mask,random_seed=18)
    for key in ['original_b64','restored_b64','cinnabar_b64','binary_skeleton_b64']:
        assert a[key]==b[key]
    assert a['original_b64']!=c['original_b64']
    assert a['metrics']['psnr'] is None and a['metrics']['ssim'] is None


def test_official_identity_cannot_be_overridden():
    response=TestClient(app).post('/api/process',json={'stele_id':'han_01_caoquan','image_base64':'data:image/png;base64,AAAA'})
    assert response.status_code==422
    assert '不能与外部图像混用' in response.json()['detail']


def test_effective_notch_stops_before_nlm_and_holes_are_not_repainted():
    y, x = np.mgrid[:256, :256]
    clean = np.full((256, 256), 80, np.uint8)
    clean[70:190, 100:130] = 190
    periodic = np.clip(clean.astype(float) + 25 * np.sin(2 * np.pi * x / 8), 0, 255).astype(np.uint8)
    _output, details = AdaptiveRubbingRestorer().restore(periodic)
    operators = [item['operator'] for item in details['decisions']]
    assert 'notch' in operators
    if 'stop_after_notch' in operators:
        assert 'nlm' not in operators and 'thin_stroke_nlm' not in operators
    image = np.full((180, 180), 40, np.uint8)
    image += np.random.default_rng(3).integers(0, 25, image.shape, dtype=np.uint8)
    image[40:90, 40:90] = 180
    painted = image.copy()
    painted[50:70, 50:70] = 20
    preserved, pixels = preserve_missing_regions(image, painted)
    assert pixels > 0
    assert np.array_equal(preserved[40:90, 40:90], image[40:90, 40:90])


def test_page_colored_whitespace_is_not_treated_as_loss_and_notch_quiets_flats():
    from degradation_analysis import missing_information_mask
    page = np.full((180, 180), 230, np.uint8)
    page[50:130, 50:130] = 30
    page[70:110, 70:110] = 230
    assert missing_information_mask(page)[80:100, 80:100].sum() == 0
    occluded = page.copy()
    occluded[70:110, 70:110] = 80
    assert missing_information_mask(occluded)[80:100, 80:100].sum() > 0
    y, x = np.mgrid[:256, :256]
    clean = np.full((256, 256), 80, np.uint8)
    clean[70:190, 100:130] = 190
    periodic = np.clip(clean.astype(float) + 25 * np.sin(2 * np.pi * x / 8), 0, 255).astype(np.uint8)
    output, details = AdaptiveRubbingRestorer().restore(periodic)
    assert 'stop_after_notch' in [item['operator'] for item in details['decisions']]
    assert output[:40, :40].std() < periodic[:40, :40].std()


def test_thin_stroke_uses_weaker_nlm_than_a_thick_stroke():
    rng = np.random.default_rng(4)
    thick = np.full((128, 128), 40, np.uint8)
    thick[30:100, 30:100] = 200
    thick = np.clip(thick.astype(float) + rng.normal(0, 12, thick.shape), 0, 255).astype(np.uint8)
    thin = np.full((128, 128), 40, np.uint8)
    thin[64, 20:110] = 220
    thin = np.clip(thin.astype(float) + rng.normal(0, 12, thin.shape), 0, 255).astype(np.uint8)
    _, thick_details = AdaptiveRubbingRestorer().restore(thick, strength=1)
    _, thin_details = AdaptiveRubbingRestorer().restore(thin, strength=1)
    thick_h = next(item['h'] for item in thick_details['decisions'] if item['operator'] in ('nlm', 'thin_stroke_nlm'))
    thin_h = next(item['h'] for item in thin_details['decisions'] if item['operator'] in ('nlm', 'thin_stroke_nlm'))
    assert thin_details['decisions']
    assert any(item['operator'] == 'thin_stroke_nlm' for item in thin_details['decisions'])
    assert thin_h < thick_h


def test_invalid_image_rejected():
    with pytest.raises(ValueError):
        analyze_degradation(np.zeros((5,5),np.uint8))
    with pytest.raises(ValueError):
        analyze_degradation(np.zeros((2000,2000),np.uint8))
