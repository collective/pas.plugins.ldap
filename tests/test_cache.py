"""Unit tests for pas.plugins.ldap.cache module."""

import time
import unittest
from unittest.mock import MagicMock, patch


class TestCacheProviderFactoryServers(unittest.TestCase):
    """Tests for cacheProviderFactory.servers — uncovered branch (line 67)."""

    def test_servers_no_record_provider(self):
        """servers returns '' when no ICacheSettingsRecordProvider is registered."""
        from pas.plugins.ldap.cache import cacheProviderFactory

        factory = cacheProviderFactory()
        with patch("pas.plugins.ldap.cache.queryUtility", return_value=None):
            result = factory.servers
        self.assertEqual(result, "")


class TestRequestPluginCacheParentRequest(unittest.TestCase):
    """Tests for RequestPluginCache.getRootRequest — uncovered branch (line 149)."""

    def test_get_root_request_follows_parent_chain(self):
        """getRootRequest() recurses through PARENT_REQUEST to reach root."""
        from pas.plugins.ldap.cache import RequestPluginCache

        context = MagicMock()
        context.getId.return_value = "testplugin"
        cache = RequestPluginCache(context)

        inner_request = {"data": "inner"}
        outer_request = {"PARENT_REQUEST": inner_request}

        with patch("pas.plugins.ldap.cache.getRequest", return_value=outer_request):
            root = cache.getRootRequest()

        self.assertIs(root, inner_request)


class TestVolatilePluginCache(unittest.TestCase):
    """Tests for VolatilePluginCache — uncovered branches (lines 192, 205-206)."""

    def test_get_returns_not_cached_when_expired(self):
        """get() returns VALUE_NOT_CACHED when the cached entry has expired."""
        from pas.plugins.ldap.cache import VOLATILE_CACHE_MAXAGE, VolatilePluginCache
        from pas.plugins.ldap.interfaces import VALUE_NOT_CACHED

        context = MagicMock()
        context.getId.return_value = "testplugin"
        cache = VolatilePluginCache(context)

        expired_time = time.time() - VOLATILE_CACHE_MAXAGE - 1
        setattr(context, cache._key, (expired_time, "stale_value"))

        result = cache.get()
        self.assertIs(result, VALUE_NOT_CACHED)

    def test_invalidate_handles_missing_attribute(self):
        """invalidate() silently ignores AttributeError when key is not set."""
        from pas.plugins.ldap.cache import VolatilePluginCache

        class SimpleContext:
            def getId(self):
                return "testplugin"

        context = SimpleContext()
        cache = VolatilePluginCache(context)
        # The cache attribute is not set on context, so delattr raises
        # AttributeError — the except branch on lines 205-206 must absorb it.
        cache.invalidate()  # Must not raise
