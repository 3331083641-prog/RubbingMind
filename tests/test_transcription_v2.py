from catalog import inference,museum_records,transcription_text


def test_administrative_pdf_headers_are_not_displayed_as_inscription():
    records={r['id']:r for r in museum_records()}
    cao=inference(records['han_01_caoquan'])
    assert cao['transcript'].startswith('君諱全')
    assert cao['characters'][0]['char']=='君'
    assert '授權與引用' not in cao['transcript']
    assert '文物統一編號' not in cao['transcript']
    assert transcription_text({'translation':'孤字。□。\x00未知。'})=='孤字。□。未知。'
