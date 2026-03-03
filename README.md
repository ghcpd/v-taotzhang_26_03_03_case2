# Integration Status Fix

## Problem

When an auto-enabling integration failed to set up during `setup_integrations()`, it would still be included in the returned dictionary of enabled integrations. This happened even though the integration never actually initialized successfully. This was confusing because:

1. The integration appeared to be "enabled" in the integrations list
2. But it never actually performed its setup due to a missing dependency or incompatibility
3. Users couldn't distinguish between successfully enabled integrations and failed ones

### Example Scenario

A `RedisIntegration` might fail if Redis client library isn't installed. Previously:
- `setup_integrations()` would catch the `DidNotEnable` exception
- The integration would still appear in the returned integrations dict
- The SDK would report the integration as enabled, even though it wasn't

## Solution

Modified [sentry_sdk/integrations/__init__.py](basecode/sentry_sdk/integrations/__init__.py) to:

1. **Track failed integrations globally** - Added a new module-level set `_failed_integrations` to track which integrations have failed to enable across multiple calls to `setup_integrations()`.

2. **Skip previously-failed integrations** - When `setup_integrations()` is called, it checks if an integration is in `_failed_integrations` and skips it immediately.

3. **Remove failed integrations from results** - When an integration raises `DidNotEnable` during setup:
   - It's added to both the local `failed_integrations` list and the global `_failed_integrations` set
   - These failed integrations are removed from the returned dictionary
   - Only genuinely enabled integrations are returned to the caller

## Changes Made

### File: `basecode/sentry_sdk/integrations/__init__.py`

1. **Added global tracking set** (line 21):
   ```python
   _failed_integrations = set()  # type: Set[str]
   ```

2. **Updated `setup_integrations()` function** (lines 120-150+):
   - Maintain a local `failed_integrations` list
   - Check if integration is already in `_failed_integrations` before setup
   - When `DidNotEnable` is caught, add to both `_failed_integrations` and local list
   - Delete all failed integrations from the `integrations` dictionary before returning

## Test Results

All tests pass with the new behavior:

```
PASSED: Failed integration correctly excluded from enabled list
PASSED: Multiple setup calls maintain consistent state

Results: 2 passed, 0 failed
```

### Test 1: `test_failed_integration_not_in_enabled_list`
- Creates both a working and failing test integration
- Verifies that the working integration is included in results
- Verifies that the failing integration is NOT included in results

### Test 2: `test_multiple_setup_calls_consistency`
- Calls `setup_integrations()` twice with the same failing integration
- Verifies that failed integrations are consistently excluded on both calls

## Backward Compatibility

The changes:
- ✅ Only affect integrations that raise `DidNotEnable` during setup
- ✅ Don't change behavior for successfully enabled integrations
- ✅ Maintain the silent-swallowing of `DidNotEnable` for default integrations
- ✅ Still raise `DidNotEnable` for explicitly provided integrations that fail

## How to Test

Run the test script:
```bash
python test_integration_status.py
```

Expected output:
```
PASSED: Failed integration correctly excluded from enabled list
PASSED: Multiple setup calls maintain consistent state

Results: 2 passed, 0 failed
```
