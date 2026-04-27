# Vault Sync Feature

The `sync` module allows you to **push** and **pull** locked vault files to and from a shared directory — such as a network mount, a cloud-synced folder (e.g. Dropbox, S3 FUSE), or a USB drive.

## How It Works

1. Lock your `.env` file into a `.vault` file with `envault lock`.
2. Push the vault to a shared location with `envault sync push`.
3. On another machine, pull the vault and unlock it.

No plaintext secrets are ever written to the shared directory — only the encrypted `.vault` blob.

## CLI Usage

### Push a vault

```bash
envault sync push <profile> --sync-dir /mnt/shared/envault
```

### Pull a vault

```bash
envault sync pull <profile> --sync-dir /mnt/shared/envault
```

Optionally specify a custom local path:

```bash
envault sync pull <profile> --sync-dir /mnt/shared/envault --vault-path ./my.vault
```

### Check what's available remotely

```bash
envault sync status --sync-dir /mnt/shared/envault
```

Example output:

```
  default              pushed_at=2024-06-01T12:00:00+00:00  size=312B
  staging              pushed_at=2024-06-01T11:45:00+00:00  size=298B
```

## Sync Manifest

A `.envault_sync` JSON file is maintained in the sync directory. It records metadata (timestamp, size) for each pushed profile. It does **not** contain any secrets.

## Security Notes

- Only encrypted vault blobs are shared — the master key is **never** written to the sync directory.
- Each team member must have the master key out-of-band (e.g. via a password manager).
- The sync directory itself should have appropriate access controls.
