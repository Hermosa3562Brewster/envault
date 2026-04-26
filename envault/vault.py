"""vault.py — Core vault operations for envault.

Provides high-level functions to lock (encrypt) and unlock (decrypt)
.env files, as well as read/write the encrypted vault format to disk.
"""

import json
import os
from pathlib import Path

from envault.crypto import derive_key, encrypt, decrypt

# Default filenames used by the CLI and sync tooling
DEFAULT_ENV_FILE = ".env"
DEFAULT_VAULT_FILE = ".env.vault"


def _parse_env(text: str) -> dict[str, str]:
    """Parse a .env file into a plain dict.

    Supports:
    - KEY=VALUE pairs
    - Lines beginning with '#' are treated as comments and ignored
    - Quoted values (single or double quotes are stripped)
    - Empty lines are skipped
    """
    env: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes if present
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        env[key] = value
    return env


def _serialize_env(env: dict[str, str]) -> str:
    """Serialize a dict back into .env file format."""
    lines = [f'{key}="{value}"' for key, value in env.items()]
    return "\n".join(lines) + "\n"


def lock(master_password: str, env_path: str | Path = DEFAULT_ENV_FILE) -> bytes:
    """Read a .env file and return an encrypted vault blob.

    The vault blob is a JSON envelope containing:
    - ``cipherblob``: hex-encoded encrypted payload
    - ``version``:    format version for future migrations

    Args:
        master_password: The password used to derive the encryption key.
        env_path:        Path to the plaintext .env file to encrypt.

    Returns:
        UTF-8 encoded JSON bytes representing the sealed vault.

    Raises:
        FileNotFoundError: If *env_path* does not exist.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        raise FileNotFoundError(f"No .env file found at '{env_path}'")

    plaintext = env_path.read_text(encoding="utf-8")
    key = derive_key(master_password)
    cipherblob = encrypt(key, plaintext.encode("utf-8"))

    envelope = {
        "version": 1,
        "cipherblob": cipherblob.hex(),
    }
    return json.dumps(envelope, indent=2).encode("utf-8")


def unlock(
    master_password: str,
    vault_data: bytes,
) -> dict[str, str]:
    """Decrypt a vault blob and return the parsed environment variables.

    Args:
        master_password: The password used to derive the decryption key.
        vault_data:      Raw bytes of the vault file (JSON envelope).

    Returns:
        A dict mapping environment variable names to their values.

    Raises:
        ValueError:  If the master password is wrong or the blob is corrupted.
        KeyError:    If the vault envelope is missing expected fields.
    """
    envelope = json.loads(vault_data.decode("utf-8"))
    cipherblob = bytes.fromhex(envelope["cipherblob"])
    key = derive_key(master_password)
    plaintext_bytes = decrypt(key, cipherblob)  # raises ValueError on bad key
    return _parse_env(plaintext_bytes.decode("utf-8"))


def save_vault(vault_data: bytes, vault_path: str | Path = DEFAULT_VAULT_FILE) -> None:
    """Write encrypted vault bytes to *vault_path*.

    The file is written with mode 0o600 so that only the owning user can
    read it — similar to how SSH private keys are stored.
    """
    vault_path = Path(vault_path)
    vault_path.write_bytes(vault_data)
    os.chmod(vault_path, 0o600)


def load_vault(vault_path: str | Path = DEFAULT_VAULT_FILE) -> bytes:
    """Read raw vault bytes from *vault_path*.

    Raises:
        FileNotFoundError: If no vault file exists at *vault_path*.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise FileNotFoundError(
            f"No vault file found at '{vault_path}'. "
            "Run 'envault lock' to create one."
        )
    return vault_path.read_bytes()
