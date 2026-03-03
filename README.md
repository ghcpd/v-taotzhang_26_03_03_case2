# Fix: Integrations That Fail Setup No Longer Reported as Enabled

## Problem

When an auto-enabling integration (e.g., `RedisIntegration`) failed during `setup_once()` by raising `DidNotEnable`, the SDK still:

1. Added the integration's identifier to `_installed_integrations`, marking it as "installed."
2. Kept the integration in the dictionary returned by `setup_integrations()`, making it appear enabled to callers.

This was misleading — the integration never actually set up, yet it showed up in the active integrations list.

## Root Cause

In `sentry_sdk/integrations/__init__.py`, the `setup_integrations` function had the line `_installed_integrations.add(identifier)` **outside** the `try/except` block, so it executed regardless of whether `setup_once()` succeeded or raised `DidNotEnable`. The failed integration also remained in the `integrations` dict that was returned.

## Fix

In `basecode/sentry_sdk/integrations/__init__.py`, the `setup_integrations` function was changed to:

- **Skip `_installed_integrations.add()`** when `DidNotEnable` is caught — the `except DidNotEnable` handler now uses `continue` to skip the rest of the loop body (including the `_installed_integrations.add(identifier)` call).
- **Remove failed integrations from the returned dict** — a `failed_integrations` set tracks identifiers that failed, and those entries are popped from the `integrations` dict before it is returned.

## Files Changed

- `basecode/sentry_sdk/integrations/__init__.py` — Fixed `setup_integrations()` to exclude failed integrations from results and from `_installed_integrations`.

## Verification

Run the test script:

```bash
python test_integration_status.py
```

Expected output:

```
PASSED: Failed integration correctly excluded from enabled list
PASSED: Multiple setup calls maintain consistent state

==================================================
Results: 2 passed, 0 failed
==================================================
```
