from carrier_verify.validate import is_valid_usdot, normalize_docket, normalize_usdot


def test_plain_number():
    assert normalize_usdot("1234567").value == "1234567"


def test_prefix_variants():
    for raw in ["USDOT 1234567", "US DOT# 1234567", "DOT:1234567", "usdot-1234567"]:
        r = normalize_usdot(raw)
        assert r.ok, raw
        assert r.value == "1234567"


def test_ocr_confusables():
    assert normalize_usdot("I23456O").value == "1234560"
    assert normalize_usdot("US DOT SS123").value == "55123"


def test_leading_zeros_stripped():
    assert normalize_usdot("0012345").value == "12345"


def test_rejects_garbage():
    assert not normalize_usdot("").ok
    assert not normalize_usdot("USDOT").ok
    assert not normalize_usdot("12X34*", correct_confusables=False).ok
    assert not normalize_usdot("123456789").ok  # 9 digits


def test_is_valid_usdot():
    assert is_valid_usdot("1")
    assert is_valid_usdot("12345678")
    assert not is_valid_usdot("0123")
    assert not is_valid_usdot("123456789")


def test_docket():
    assert normalize_docket("MC-123456").value == "MC123456"
    assert normalize_docket("mc 000123").value == "MC123"
    assert normalize_docket("FF#4567").value == "FF4567"
    assert not normalize_docket("XX123").ok
