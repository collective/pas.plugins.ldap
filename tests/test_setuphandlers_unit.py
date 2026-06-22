"""Pure unit tests for pas.plugins.ldap.setuphandlers module.

These tests exercise all branches of setuphandlers.py using unittest.mock
so no real LDAP server, Zope layer, or GenericSetup context is needed.
"""

from pas.plugins.ldap.setuphandlers import _addPlugin
from pas.plugins.ldap.setuphandlers import post_install
from pas.plugins.ldap.setuphandlers import remove_persistent_import_step
from pas.plugins.ldap.setuphandlers import TITLE
from unittest.mock import MagicMock
from unittest.mock import patch

import unittest


# ---------------------------------------------------------------------------
# remove_persistent_import_step  (lines 28-31)
# ---------------------------------------------------------------------------


class TestRemovePersistentImportStep(unittest.TestCase):
    """Tests for remove_persistent_import_step."""

    def _make_context(self, has_step=False):
        """Return a mock GenericSetup context."""
        registry = MagicMock()
        if has_step:
            registry._registered = {"pas.plugins.ldap.setup": object()}
        else:
            registry._registered = {}
        context = MagicMock()
        context.getImportStepRegistry.return_value = registry
        return context, registry

    def test_unregisters_step_when_present(self):
        """Calls unregisterStep when the import step is in _registered (line 31)."""
        context, registry = self._make_context(has_step=True)
        remove_persistent_import_step(context)
        registry.unregisterStep.assert_called_once_with("pas.plugins.ldap.setup")

    def test_does_not_unregister_when_step_absent(self):
        """Does NOT call unregisterStep when the import step is not present (line 30 branch)."""
        context, registry = self._make_context(has_step=False)
        remove_persistent_import_step(context)
        registry.unregisterStep.assert_not_called()

    def test_calls_getImportStepRegistry(self):
        """Always calls context.getImportStepRegistry() (line 28)."""
        context, _ = self._make_context()
        remove_persistent_import_step(context)
        context.getImportStepRegistry.assert_called_once()


# ---------------------------------------------------------------------------
# _addPlugin  (lines 34-50)
# ---------------------------------------------------------------------------


class TestAddPlugin(unittest.TestCase):
    """Tests for _addPlugin helper."""

    def _make_pas(self, installed=None):
        """Return a mock PAS instance."""
        pas = MagicMock()
        pas.objectIds.return_value = installed or []
        return pas

    def test_returns_already_installed_message_when_plugin_exists(self):
        """Returns 'already installed' message when pluginid is in objectIds (lines 38-39)."""
        pas = self._make_pas(installed=["pasldap"])
        result = _addPlugin(pas)
        self.assertIn("already installed", result)
        self.assertEqual(result, TITLE + " already installed.")

    def test_logs_info_when_plugin_already_installed(self):
        """Logs info message when plugin already present (line 38)."""
        pas = self._make_pas(installed=["pasldap"])
        with patch("pas.plugins.ldap.setuphandlers.logger") as mock_logger:
            _addPlugin(pas)
        mock_logger.info.assert_called_once()
        args = mock_logger.info.call_args[0]
        self.assertIn("pasldap", args[1])

    def test_already_installed_with_custom_pluginid(self):
        """Works with a custom pluginid (line 37 branch)."""
        pas = self._make_pas(installed=["myplugin"])
        result = _addPlugin(pas, pluginid="myplugin")
        self.assertIn("already installed", result)

    def test_installs_plugin_when_not_present(self):
        """Creates plugin and calls _setObject when pluginid is not installed (lines 40-50)."""
        pas = self._make_pas(installed=[])
        # No interfaces provide the plugin, so the loop body is skipped
        pas.plugins.listPluginTypeInfo.return_value = []

        with patch("pas.plugins.ldap.setuphandlers.LDAPPlugin") as MockPlugin:
            mock_plugin_instance = MagicMock()
            mock_plugin_instance.getId.return_value = "pasldap"
            MockPlugin.return_value = mock_plugin_instance
            pas.__getitem__ = MagicMock(return_value=mock_plugin_instance)
            _addPlugin(pas)

        pas._setObject.assert_called_once()
        MockPlugin.assert_called_once_with("pasldap", title=TITLE)

    def test_activates_interfaces_provided_by_plugin(self):
        """Activates and reorders plugin for each matching interface (lines 45-50)."""
        pas = self._make_pas(installed=[])
        mock_iface = MagicMock()
        mock_iface.providedBy.return_value = True
        pas.plugins.listPluginTypeInfo.return_value = [{"interface": mock_iface}]
        pas.plugins.listPlugins.return_value = [("pasldap", MagicMock())]

        with patch("pas.plugins.ldap.setuphandlers.LDAPPlugin") as MockPlugin:
            mock_plugin_instance = MagicMock()
            mock_plugin_instance.getId.return_value = "pasldap"
            MockPlugin.return_value = mock_plugin_instance
            pas.__getitem__ = MagicMock(return_value=mock_plugin_instance)
            _addPlugin(pas)

        pas.plugins.activatePlugin.assert_called_once_with(mock_iface, "pasldap")
        pas.plugins.movePluginsDown.assert_called_once()

    def test_skips_interface_not_provided_by_plugin(self):
        """Skips interface when plugin does not provide it (line 46 continue branch)."""
        pas = self._make_pas(installed=[])
        mock_iface = MagicMock()
        mock_iface.providedBy.return_value = False  # not provided → continue
        pas.plugins.listPluginTypeInfo.return_value = [{"interface": mock_iface}]

        with patch("pas.plugins.ldap.setuphandlers.LDAPPlugin") as MockPlugin:
            mock_plugin_instance = MagicMock()
            mock_plugin_instance.getId.return_value = "pasldap"
            MockPlugin.return_value = mock_plugin_instance
            pas.__getitem__ = MagicMock(return_value=mock_plugin_instance)
            _addPlugin(pas)

        pas.plugins.activatePlugin.assert_not_called()
        pas.plugins.movePluginsDown.assert_not_called()


# ---------------------------------------------------------------------------
# post_install  (lines 53-57)
# ---------------------------------------------------------------------------


class TestPostInstall(unittest.TestCase):
    """Tests for post_install."""

    def test_calls_addPlugin_with_acl_users(self):
        """post_install gets the site, accesses acl_users and calls _addPlugin (lines 55-57)."""
        mock_pas = MagicMock()
        mock_site = MagicMock()
        mock_site.acl_users = mock_pas

        with patch("pas.plugins.ldap.setuphandlers.getSite", return_value=mock_site):
            with patch("pas.plugins.ldap.setuphandlers._addPlugin") as mock_add:
                post_install(MagicMock())

        mock_add.assert_called_once_with(mock_pas)

    def test_uses_getSite_to_get_site(self):
        """post_install calls getSite() (line 55)."""
        mock_site = MagicMock()

        with (
            patch(
                "pas.plugins.ldap.setuphandlers.getSite", return_value=mock_site
            ) as mock_get_site,
            patch("pas.plugins.ldap.setuphandlers._addPlugin"),
        ):
            post_install(MagicMock())

        mock_get_site.assert_called_once()
