import pytest

from aceest.auth import safe_next_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/dashboard", "/dashboard"),
        ("/clients?x=1", "/clients?x=1"),
        (None, None),
        ("", None),
        ("http://evil.com", None),
        ("//evil.com/phish", None),
        ("\\\\evil", None),
    ],
)
def test_safe_next_url_only_allows_relative_paths(raw, expected):
    assert safe_next_url(raw) == expected
