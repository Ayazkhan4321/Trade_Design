from Create_Account import country_utils as cu


def test_format_display_with_dial():
    c = {"name": "India", "dial_code": "+91", "code": "IN"}
    assert cu.format_country_display(c) == "+91 India"


def test_format_display_without_dial():
    c = {"name": "France", "code": "FR"}
    assert cu.format_country_display(c) == "France"


def test_normalize_country_valid():
    c = {"name": "UK", "dial_code": "+44", "code": "GB", "extra": "ignore"}
    n = cu.normalize_country_data(c)
    assert n == {"name": "UK", "dial_code": "+44", "code": "GB"}


def test_normalize_country_invalid():
    c = {"caption": "Unknown"}
    assert cu.normalize_country_data(c) is None
