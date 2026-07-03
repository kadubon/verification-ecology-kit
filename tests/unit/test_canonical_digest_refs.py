from __future__ import annotations

import pytest

from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.digest import Digest, DigestPolicy, object_digest_input
from verification_ecology_kit.errors import ErrorCode, VEKError
from verification_ecology_kit.references import ObjectEnvelope, ReferenceResolver, resolve_pointer


def test_canonicalization_is_deterministic_for_key_order() -> None:
    canonicalizer = Canonicalizer()
    left = canonicalizer.canonicalize({"b": 2, "a": [1, True]})
    right = canonicalizer.canonicalize({"a": [1, True], "b": 2})
    assert left == right


def test_duplicate_members_fail_on_load() -> None:
    with pytest.raises(VEKError) as exc:
        Canonicalizer().loads('{"a": 1, "a": 2}')
    assert exc.value.code == ErrorCode.DUPLICATE_MEMBER


def test_invalid_unicode_surrogate_fails() -> None:
    with pytest.raises(VEKError) as exc:
        Canonicalizer().canonicalize({"bad": "\ud800"})
    assert exc.value.code == ErrorCode.INVALID_UNICODE


def test_non_interoperable_integer_fails() -> None:
    with pytest.raises(VEKError) as exc:
        Canonicalizer().canonicalize({"n": 2**60})
    assert exc.value.code == ErrorCode.NON_INTEROPERABLE_NUMBER


def test_digest_stability_and_envelope_refresh() -> None:
    envelope = ObjectEnvelope("o1", "schema", "1.0", {"x": 1})
    digest = envelope.refresh_digest()
    assert digest.value
    expected = DigestPolicy().digest_json(object_digest_input(envelope.to_dict()))
    assert expected.value == envelope.canonical_digest.value


def test_json_pointer_resolution() -> None:
    document = {"a": {"b/c": [10, 20]}}
    assert resolve_pointer(document, "/a/b~1c/1") == 20


def test_reference_resolver_detects_digest_mismatch() -> None:
    envelope = ObjectEnvelope("o1", "schema", "1.0", {"x": 1})
    envelope.refresh_digest()
    ref = envelope.ref(bundle_id="b")
    bad_ref = type(ref)(
        bundle_id=ref.bundle_id,
        object_id=ref.object_id,
        schema_id=ref.schema_id,
        pointer=ref.pointer,
        digest_algorithm_id=ref.digest_algorithm_id,
        digest=Digest("sha256", "0" * 64),
        intended_use=ref.intended_use,
    )
    _, _, result = ReferenceResolver(bundle_id="b", envelopes=[envelope]).resolve(bad_ref)
    assert not result.passed
