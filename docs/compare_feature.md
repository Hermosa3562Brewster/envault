# Profile & Vault Comparison

The `compare` feature lets you diff two vault profiles (or raw vault files) side-by-side to spot configuration drift between environments.

## Commands

### Compare two named profiles

```bash
envault compare profiles staging production --key $MASTER_KEY
```

Outputs keys that differ between the two profiles:

```
Comparing 'staging' vs 'production':
  < DEBUG=true  (only in staging)
  ~ DB_HOST: staging='db-dev.internal'  production='db-prod.internal'
  > SENTRY_DSN=https://...  (only in production)
```

Exits with code `1` if any differences are found, making it suitable for CI checks.

### Compare two vault files directly

```bash
envault compare files path/to/left.vault path/to/right.vault --key $MASTER_KEY \
  --left-label before --right-label after
```

Useful for comparing a snapshot against the live vault without registering profiles.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | No differences found |
| 1    | One or more differences detected |
| 2    | Error (missing file, bad key, unknown profile) |

## Programmatic Usage

```python
from envault.compare import compare_profiles, summary_lines

result = compare_profiles("staging", "production", master_key=key)
if result.has_differences:
    for line in summary_lines(result, left_label="staging", right_label="production"):
        print(line)
```

## Integration with CI

Add a step to your pipeline to catch environment drift before deploying:

```yaml
- name: Check env parity
  run: envault compare profiles staging production --key $MASTER_KEY
  env:
    MASTER_KEY: ${{ secrets.ENVAULT_MASTER_KEY }}
```
