"""Tests for the abstract adapter protocol."""

import inspect

import pytest

from voyage_framework.core.adapter_protocols import AdapterProtocol


def test_protocol_is_abstract():
    assert inspect.isabstract(AdapterProtocol)
    with pytest.raises(TypeError):
        AdapterProtocol()


def test_expected_methods():
    assert AdapterProtocol.__abstractmethods__ == {
        "validate_request",
        "create_task",
        "get_context",
        "request_prompt",
        "submit_result",
        "request_approval",
    }


@pytest.mark.parametrize("name", AdapterProtocol.__abstractmethods__)
def test_each_method_abstract(name: str):
    assert getattr(AdapterProtocol, name).__isabstractmethod__ is True
