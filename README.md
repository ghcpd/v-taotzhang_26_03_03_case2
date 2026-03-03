# Integration Setup Fix

This repository contains a minimal reproduction of an issue with the Sentry
Python SDK's integration handling.

## Problem

Default integrations that auto-enable during SDK initialization would still be
reported as "enabled" even if their `setup_once()` method raised
`DidNotEnable`. That exception is raised when the integration cannot be activated
because of missing dependencies or incompatible versions. Even though the
integration never actually hooked anything, it remained in the return value of
`setup_integrations()` and in the `_installed_integrations` set. This led to
confusion for users inspecting which integrations are active.

## Change

The `setup_integrations()` function in
`basecode/sentry_sdk/integrations/__init__.py` was updated so that:

* If a default integration raises `DidNotEnable`, it is skipped entirely and
  removed from the returned integrations mapping.
* The failing integration is **not** added to `_installed_integrations` so
  subsequent calls will attempt to initialize it again (and continue to omit it
  from results).
* Logging was adjusted to avoid reporting skipped integrations as enabled.

Explicit integrations (ones passed by the user) still propagate the exception
when `DidNotEnable` is raised, preserving the previous behaviour.

## Verification

A small test script (`test_integration_status.py`) exercises the bug by
simulating a working integration and one that always fails. Both of the
provided tests now pass:

```bash
python test_integration_status.py
```

After the fix the failing integration is no longer listed and repeated calls
remain consistent.

## Why it matters

Accurate reporting of enabled integrations helps users diagnose SDK
configuration issues. By filtering out failures we prevent misleading status
information and avoid memory growth in the installation set.

The patch is isolated and backwards compatible with existing behaviour for
explicit integrations.