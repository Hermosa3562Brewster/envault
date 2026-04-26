"""Tests for envault.crypto encryption / decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt, SALT_SIZE


MASTER_KEY = "super-secret-master-key-42"
ALT_KEY = "wrong-key"
SAMPLE_ENV = "DB_URL=postgres://localhost/mydb\nSECRET=abc123\n"


def test_encrypt_returns_bytes():
    result = encrypt(SAMPLE_ENV, MASTER_KEY)
    assert isinstance(result, bytes)


def test_cipherblob_longer_than_salt():
    result = encrypt(SAMPLE_ENV, MASTER_KEY)
    assert len(result) > SALT_SIZE


def test_round_trip():
    blob = encrypt(SAMPLE_ENV, MASTER_KEY)
    recovered = decrypt(blob, MASTER_KEY)
    assert recovered == SAMPLE_ENV


def test_each_encryption_produces_unique_blob():
    blob1 = encrypt(SAMPLE_ENV, MASTER_KEY)
    blob2 = encrypt(SAMPLE_ENV, MASTER_KEY)
    assert blob1 != blob2  # different salts each time


def test_wrong_key_raises_value_error():
    blob = encrypt(SAMPLE_ENV, MASTER_KEY)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(blob, ALT_KEY)


def test_corrupted_blob_raises_value_error():
    blob = bytearray(encrypt(SAMPLE_ENV, MASTER_KEY))
    blob[20] ^= 0xFF  # flip a byte in the token
    with pytest.raises(ValueError):
        decrypt(bytes(blob), MASTER_KEY)


def test_too_short_blob_raises_value_error():
    with pytest.raises(ValueError, match="too short"):
        decrypt(b"short", MASTER_KEY)


def test_empty_string_round_trip():
    blob = encrypt("", MASTER_KEY)
    assert decrypt(blob, MASTER_KEY) == ""
