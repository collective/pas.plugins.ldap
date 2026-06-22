"""Unit tests for pas.plugins.ldap.plonecontrolpanel modules."""

from unittest.mock import patch

import unittest


class TestHiddenProfiles(unittest.TestCase):
    """Tests for HiddenProfiles — uncovered branches (return statements)."""

    def _makeOne(self):
        from pas.plugins.ldap.plonecontrolpanel import HiddenProfiles

        return HiddenProfiles()

    def test_get_non_installable_products_returns_hidden_list(self):
        """getNonInstallableProducts() returns the list of hidden profiles."""
        obj = self._makeOne()
        result = obj.getNonInstallableProducts()
        self.assertIn("pas.plugins.ldap:default", result)
        self.assertIn("pas.plugins.ldap.plonecontrolpanel:install-base", result)

    def test_get_non_installable_profiles_returns_hidden_list(self):
        """getNonInstallableProfiles() returns the list of hidden profiles."""
        obj = self._makeOne()
        result = obj.getNonInstallableProfiles()
        self.assertIn("pas.plugins.ldap:default", result)
        self.assertIn("pas.plugins.ldap.plonecontrolpanel:install-base", result)


class TestCacheSettingsRecordProvider(unittest.TestCase):
    """Tests for CacheSettingsRecordProvider — uncovered branch (line 29)."""

    def _makeOne(self):
        from pas.plugins.ldap.plonecontrolpanel.cache import CacheSettingsRecordProvider

        return CacheSettingsRecordProvider()

    def test_call_returns_null_record_when_no_registry(self):
        """__call__() returns NullRecord when IRegistry utility is not registered."""
        from pas.plugins.ldap.plonecontrolpanel.cache import NullRecord

        provider = self._makeOne()
        with patch(
            "pas.plugins.ldap.plonecontrolpanel.cache.queryUtility", return_value=None
        ):
            result = provider()
        self.assertIsInstance(result, NullRecord)
        self.assertEqual(result.value, "")
