import pytest
from pydantic import ValidationError

from app.schemas.scan import ScanRequest


def test_target_starting_with_dash_is_rejected():
    with pytest.raises(ValidationError):
        ScanRequest(target="-oN=/tmp/evil", port=80, scheme="http")


def test_normal_target_is_accepted():
    request = ScanRequest(target="juice-shop", port=80, scheme="http")
    assert request.target == "juice-shop"
