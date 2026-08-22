import pytest
from pydantic import ValidationError

from app.schemas.scan import ScanRequest


def test_target_starting_with_dash_is_rejected():
    with pytest.raises(ValidationError):
        ScanRequest(target="-oN=/tmp/evil", port=80, scheme="http")


def test_normal_target_is_accepted():
    request = ScanRequest(target="juice-shop", port=80, scheme="http")
    assert request.target == "juice-shop"


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("ports", "-oN=/tmp/evil"),
        ("severity", "-update-templates"),
        ("tags", "-config=evil"),
        ("max_time", "-h"),
        ("aggression", "-oX-"),
    ],
)
def test_option_value_starting_with_dash_is_rejected(key, bad_value):
    with pytest.raises(ValidationError):
        ScanRequest(target="juice-shop", port=80, scheme="http", options={key: bad_value})


def test_aggression_as_negative_int_is_also_rejected():
    # aggression is normally an int (WhatWebAdapter does str(options.get(
    # "aggression", 3))), not a str like the other guarded keys — confirm
    # the guard still catches it via str(value) rather than only matching
    # when the raw value itself is already a string starting with "-".
    with pytest.raises(ValidationError):
        ScanRequest(target="juice-shop", port=80, scheme="http", options={"aggression": -1})


def test_normal_options_are_accepted():
    request = ScanRequest(
        target="juice-shop",
        port=80,
        scheme="http",
        options={"ports": "1-1000", "severity": "high", "tags": "cve", "max_time": "120s", "aggression": 3},
    )
    assert request.options["ports"] == "1-1000"
