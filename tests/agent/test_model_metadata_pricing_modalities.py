"""Regression tests for #158208: list-valued ``modalities`` alongside ``pricing``
must not break endpoint model-metadata parsing.
"""

from agent.model_metadata import _extract_pricing, _parse_models_payload


PRICING = {
    "prompt": "0.0000025",
    "completion": "0.00001",
    "input_cache_read": "0.00000025",
    "input_cache_write": "0.000003125",
}


def _model(with_modalities: bool) -> dict:
    model = {
        "id": "custom-model",
        "object": "model",
        "context_length": 128000,
        "pricing": PRICING,
    }
    if with_modalities:
        model["modalities"] = {"input": ["text", "image"], "output": ["text"]}
    return model


def test_extract_pricing_ignores_list_valued_modalities():
    pricing = _extract_pricing(_model(with_modalities=True))

    assert pricing["prompt"] == PRICING["prompt"]
    assert pricing["completion"] == PRICING["completion"]
    assert all(not isinstance(value, list) for value in pricing.values())


def test_parse_models_payload_with_modalities_keeps_pricing():
    cache = _parse_models_payload(
        {"object": "list", "data": [_model(with_modalities=True)]}
    )

    assert "custom-model" in cache
    assert cache["custom-model"]["pricing"]["prompt"] == PRICING["prompt"]
    assert cache["custom-model"]["context_length"] == 128000


def test_modalities_only_payload_does_not_invent_pricing():
    payload = {
        "object": "list",
        "data": [
            {
                "id": "custom-model",
                "modalities": {"input": ["text", "image"], "output": ["text"]},
            }
        ],
    }

    assert _parse_models_payload(payload)["custom-model"].get("pricing") is None
