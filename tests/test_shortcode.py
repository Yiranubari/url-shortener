from app.core.shortcode import ALPHABET, LENGTH, generate_short_code


def test_generate_short_code_has_expected_length():
    assert len(generate_short_code()) == LENGTH


def test_generate_short_code_uses_base62_alphabet():
    code = generate_short_code()
    assert all(c in ALPHABET for c in code)


def test_generate_short_code_is_unique_across_many_calls():
    codes = {generate_short_code() for _ in range(1000)}
    assert len(codes) == 1000
