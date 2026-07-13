from scripts.load_data import parse_float, parse_int


def test_parse_float_accepts_decimal_comma():
    assert parse_float("45,5") == 45.5


def test_parse_float_rejects_bad_values():
    assert parse_float("not-a-number") is None


def test_parse_int_only_accepts_whole_numbers():
    assert parse_int("3") == 3
    assert parse_int("2.5") is None
