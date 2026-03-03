"""
Test script to verify that integrations correctly report their enabled status.
When an integration cannot be enabled during setup, it should not appear
in the list of active integrations.
"""
import sys
import os
from unittest import mock

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Check if we're in basecode or one level above, adjust accordingly
if os.path.exists(os.path.join(script_dir, "sentry_sdk")):
    # We're at the same level as sentry_sdk
    sys.path.insert(0, script_dir)
elif os.path.exists(os.path.join(script_dir, "basecode", "sentry_sdk")):
    # We're one level above (in main folder)
    sys.path.insert(0, os.path.join(script_dir, "basecode"))
else:
    raise RuntimeError("Cannot find sentry_sdk directory")

from sentry_sdk.integrations import (
    Integration,
    DidNotEnable,
    setup_integrations,
    _installed_integrations,
)


class AlwaysFailingIntegration(Integration):
    """A test integration that always fails to enable."""
    identifier = "always_failing"

    @staticmethod
    def setup_once():
        # Simulate an integration that cannot be enabled
        # (e.g., required library not installed, version incompatible)
        raise DidNotEnable("Test integration intentionally fails to enable")


class WorkingIntegration(Integration):
    """A test integration that successfully enables."""
    identifier = "working"

    @staticmethod
    def setup_once():
        # This integration sets up successfully
        pass


def mock_iter_default_integrations(with_auto_enabling):
    """Mock iterator that returns our test integrations as default ones."""
    yield WorkingIntegration
    yield AlwaysFailingIntegration


def test_failed_integration_not_in_enabled_list():
    """
    Test that integrations which raise DidNotEnable during setup_once()
    are NOT included in the returned integrations dictionary.
    
    This simulates the scenario where an auto-enabling integration
    (like RedisIntegration) fails to enable because its dependency
    is not installed or incompatible.
    """
    # Clear any previously installed integrations
    _installed_integrations.clear()
    
    # Patch iter_default_integrations to return our test integrations
    with mock.patch(
        'sentry_sdk.integrations.iter_default_integrations',
        mock_iter_default_integrations
    ):
        enabled_integrations = setup_integrations(
            integrations=[],  # No explicit integrations
            with_defaults=True,
            with_auto_enabling_integrations=True
        )
    
    # The working integration should be enabled
    assert "working" in enabled_integrations, (
        "Working integration should be in enabled integrations"
    )
    
    # The failing integration should NOT be in the enabled list
    # because it raised DidNotEnable during setup
    assert "always_failing" not in enabled_integrations, (
        "Integration that raised DidNotEnable should NOT be in enabled integrations"
    )
    
    print("PASSED: Failed integration correctly excluded from enabled list")


def test_multiple_setup_calls_consistency():
    """
    Test that calling setup_integrations multiple times with the same
    failing integration maintains correct enabled state.
    """
    # Clear any previously installed integrations
    _installed_integrations.clear()
    
    # Patch to only return our failing integration
    def iter_failing_only(with_auto):
        yield AlwaysFailingIntegration
    
    with mock.patch(
        'sentry_sdk.integrations.iter_default_integrations',
        iter_failing_only
    ):
        # First call
        result1 = setup_integrations([], with_defaults=True)
        
        # Second call
        result2 = setup_integrations([], with_defaults=True)
    
    # Neither call should have the failing integration in results
    assert "always_failing" not in result1, (
        "First call: failing integration should not be in results"
    )
    assert "always_failing" not in result2, (
        "Second call: failing integration should not be in results"
    )
    
    print("PASSED: Multiple setup calls maintain consistent state")


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_failed_integration_not_in_enabled_list,
        test_multiple_setup_calls_consistency,
    ]
    
    failed = 0
    passed = 0
    
    for test in tests:
        try:
            # Reset state before each test
            _installed_integrations.clear()
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAILED: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}")
            print(f"  Exception: {e}")
            failed += 1
    
    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
