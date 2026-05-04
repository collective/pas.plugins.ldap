"""Pure unit tests for pas.plugins.ldap.sheet module.

These tests exercise all branches of sheet.py using unittest.mock so no
real LDAP server, Zope layer, or acquisition context is needed.
"""

import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_bare_sheet(properties=None, principal_type="users", principal_id="uid0", context_raises=False):
    """Create a LDAPUserPropertySheet bypassing __init__, with full state set."""
    from pas.plugins.ldap.sheet import LDAPUserPropertySheet

    sheet = LDAPUserPropertySheet.__new__(LDAPUserPropertySheet)
    sheet._properties = dict(properties or {"mail": "old@example.com"})
    sheet._attrmap = dict(properties or {"mail": "mail"})
    sheet._ldapprincipal_type = principal_type
    sheet._ldapprincipal_id = principal_id

    mock_plugin = MagicMock()
    mock_ldap_principal = MagicMock()
    if context_raises:
        mock_ldap_principal.context.side_effect = Exception("ctx_error")

    mock_plugin.users.__getitem__.return_value = mock_ldap_principal
    mock_plugin.groups.__getitem__.return_value = mock_ldap_principal
    sheet._plugin = mock_plugin

    return sheet, mock_ldap_principal


def _build_init_sheet(user_in_users=True, attrmap=None, request=None):
    """
    Fully instantiate LDAPUserPropertySheet with all external dependencies
    mocked so that no Zope/LDAP infrastructure is required.
    """
    from pas.plugins.ldap.sheet import LDAPUserPropertySheet

    if attrmap is None:
        attrmap = {"mail": "mail", "cn": "cn"}

    principal = MagicMock()
    principal.getId.return_value = "uid0"

    plugin = MagicMock()
    plugin.getId.return_value = "ldapplugin"
    # `"uid0" in plugin.users` → user_in_users
    plugin.users.__contains__.return_value = user_in_users

    mock_pcfg = MagicMock()
    mock_pcfg.attrmap.items.return_value = list(attrmap.items())

    mock_ldap_principal = MagicMock()
    mock_ldap_principal.attrs.get.side_effect = lambda k, default="": f"v_{k}"
    plugin.users.__getitem__.return_value = mock_ldap_principal
    plugin.groups.__getitem__.return_value = mock_ldap_principal

    with patch("pas.plugins.ldap.sheet.aq_base", side_effect=lambda x: x), \
         patch("pas.plugins.ldap.sheet.ILDAPUsersConfig", return_value=mock_pcfg), \
         patch("pas.plugins.ldap.sheet.ILDAPGroupsConfig", return_value=mock_pcfg), \
         patch("pas.plugins.ldap.sheet.getRequest", return_value=request), \
         patch("pas.plugins.ldap.sheet.UserPropertySheet.__init__", return_value=None):
        sheet = LDAPUserPropertySheet(principal, plugin)

    return sheet, plugin, mock_ldap_principal, mock_pcfg


# ---------------------------------------------------------------------------
# __init__  (lines 32-58)
# ---------------------------------------------------------------------------

class TestLDAPUserPropertySheetInit(unittest.TestCase):
    """Tests for LDAPUserPropertySheet.__init__."""

    # --- user / group branch (lines 36-41) ---

    def test_init_user_branch_sets_type_to_users(self):
        """When id is in plugin.users, _ldapprincipal_type = 'users' (lines 36-38)."""
        sheet, _, _, _ = _build_init_sheet(user_in_users=True)
        self.assertEqual(sheet._ldapprincipal_type, "users")

    def test_init_group_branch_sets_type_to_groups(self):
        """When id NOT in plugin.users, _ldapprincipal_type = 'groups' (lines 40-41)."""
        sheet, _, _, _ = _build_init_sheet(user_in_users=False)
        self.assertEqual(sheet._ldapprincipal_type, "groups")

    def test_init_uses_ILDAPUsersConfig_for_user(self):
        """ILDAPUsersConfig(plugin) is called for user principals (line 37)."""
        with patch("pas.plugins.ldap.sheet.aq_base", side_effect=lambda x: x), \
             patch("pas.plugins.ldap.sheet.ILDAPUsersConfig") as mock_cfg, \
             patch("pas.plugins.ldap.sheet.ILDAPGroupsConfig"), \
             patch("pas.plugins.ldap.sheet.getRequest", return_value=None), \
             patch("pas.plugins.ldap.sheet.UserPropertySheet.__init__", return_value=None):
            from pas.plugins.ldap.sheet import LDAPUserPropertySheet
            principal = MagicMock()
            principal.getId.return_value = "uid0"
            plugin = MagicMock()
            plugin.getId.return_value = "ldapplugin"
            plugin.users.__contains__.return_value = True
            mock_pcfg = MagicMock()
            mock_pcfg.attrmap.items.return_value = []
            mock_cfg.return_value = mock_pcfg
            plugin.users.__getitem__.return_value = MagicMock()
            LDAPUserPropertySheet(principal, plugin)
        mock_cfg.assert_called_once_with(plugin)

    def test_init_uses_ILDAPGroupsConfig_for_group(self):
        """ILDAPGroupsConfig(plugin) is called for group principals (line 40)."""
        with patch("pas.plugins.ldap.sheet.aq_base", side_effect=lambda x: x), \
             patch("pas.plugins.ldap.sheet.ILDAPUsersConfig"), \
             patch("pas.plugins.ldap.sheet.ILDAPGroupsConfig") as mock_cfg, \
             patch("pas.plugins.ldap.sheet.getRequest", return_value=None), \
             patch("pas.plugins.ldap.sheet.UserPropertySheet.__init__", return_value=None):
            from pas.plugins.ldap.sheet import LDAPUserPropertySheet
            principal = MagicMock()
            principal.getId.return_value = "uid0"
            plugin = MagicMock()
            plugin.getId.return_value = "ldapplugin"
            plugin.users.__contains__.return_value = False
            mock_pcfg = MagicMock()
            mock_pcfg.attrmap.items.return_value = []
            mock_cfg.return_value = mock_pcfg
            plugin.groups.__getitem__.return_value = MagicMock()
            LDAPUserPropertySheet(principal, plugin)
        mock_cfg.assert_called_once_with(plugin)

    # --- attrmap loop (lines 42-46) ---

    def test_init_attrmap_skips_rdn_key(self):
        """'rdn' key is skipped in attrmap (lines 42-45)."""
        sheet, _, _, _ = _build_init_sheet(attrmap={"rdn": "uid", "mail": "mail"})
        self.assertNotIn("rdn", sheet._attrmap)

    def test_init_attrmap_skips_id_key(self):
        """'id' key is skipped in attrmap (lines 43-45)."""
        sheet, _, _, _ = _build_init_sheet(attrmap={"id": "uid", "mail": "mail"})
        self.assertNotIn("id", sheet._attrmap)

    def test_init_attrmap_includes_other_keys(self):
        """Non-rdn/id keys are added to _attrmap (line 46)."""
        sheet, _, _, _ = _build_init_sheet(attrmap={"mail": "mail", "cn": "cn"})
        self.assertIn("mail", sheet._attrmap)
        self.assertIn("cn", sheet._attrmap)

    # --- request handling (lines 48-53) ---

    def test_init_no_request_calls_context_load(self):
        """With request=None, attrs.context.load() is called (lines 50-51)."""
        sheet, _, mock_ldap_principal, _ = _build_init_sheet(
            request=None, attrmap={"mail": "mail"}
        )
        mock_ldap_principal.attrs.context.load.assert_called_once()

    def test_init_no_request_does_not_set_reload_flag(self):
        """With request=None, _ldap_props_reloaded is NOT set (line 52 False branch)."""
        request = None
        sheet, _, _, _ = _build_init_sheet(request=request, attrmap={"mail": "mail"})
        # No exception means the code didn't try to set the item on None

    def test_init_request_not_reloaded_sets_flag(self):
        """With a fresh request, loads attrs and sets _ldap_props_reloaded (lines 50-53)."""
        request = MagicMock()
        request.get.return_value = None  # not yet reloaded → falsy
        sheet, _, mock_ldap_principal, _ = _build_init_sheet(
            request=request, attrmap={"mail": "mail"}
        )
        mock_ldap_principal.attrs.context.load.assert_called_once()
        request.__setitem__.assert_called_with("_ldap_props_reloaded", 1)

    def test_init_request_already_reloaded_skips_load(self):
        """With a reloaded request, skips attrs.context.load (line 50 False branch)."""
        request = MagicMock()
        request.get.return_value = 1  # already reloaded → truthy
        sheet, _, mock_ldap_principal, _ = _build_init_sheet(
            request=request, attrmap={"mail": "mail"}
        )
        mock_ldap_principal.attrs.context.load.assert_not_called()

    # --- property loading (lines 54-58) ---

    def test_init_loads_properties_from_ldap_attrs(self):
        """Properties are loaded from ldapprincipal.attrs for each attrmap key (lines 54-55)."""
        sheet, _, mock_ldap_principal, _ = _build_init_sheet(
            attrmap={"mail": "mail"}, request=None
        )
        mock_ldap_principal.attrs.get.assert_called_with("mail", "")

    def test_init_calls_userpropertysheet_init(self):
        """UserPropertySheet.__init__ is called at the end of __init__ (line 56)."""
        with patch("pas.plugins.ldap.sheet.aq_base", side_effect=lambda x: x), \
             patch("pas.plugins.ldap.sheet.ILDAPUsersConfig") as mock_cfg, \
             patch("pas.plugins.ldap.sheet.ILDAPGroupsConfig"), \
             patch("pas.plugins.ldap.sheet.getRequest", return_value=None), \
             patch("pas.plugins.ldap.sheet.UserPropertySheet.__init__", return_value=None) as mock_up_init:
            from pas.plugins.ldap.sheet import LDAPUserPropertySheet
            principal = MagicMock()
            principal.getId.return_value = "uid0"
            plugin = MagicMock()
            plugin.getId.return_value = "ldapplugin"
            plugin.users.__contains__.return_value = True
            mock_pcfg = MagicMock()
            mock_pcfg.attrmap.items.return_value = []
            mock_cfg.return_value = mock_pcfg
            plugin.users.__getitem__.return_value = MagicMock()
            LDAPUserPropertySheet(principal, plugin)
        mock_up_init.assert_called_once()

    def test_init_stores_principal_id(self):
        """_ldapprincipal_id is set from principal.getId() (line 35)."""
        sheet, _, _, _ = _build_init_sheet()
        self.assertEqual(sheet._ldapprincipal_id, "uid0")

    def test_init_combined_rdn_and_other_keys(self):
        """Mixed attrmap: skips rdn/id, keeps others; covers lines 43-46."""
        sheet, _, _, _ = _build_init_sheet(
            attrmap={"rdn": "uid", "id": "uid", "mail": "mail", "cn": "cn"},
            request=None,
        )
        self.assertEqual(sheet._attrmap, {"mail": "mail", "cn": "cn"})


# ---------------------------------------------------------------------------
# _get_ldap_principal  (lines 66-67)
# ---------------------------------------------------------------------------

class TestGetLDAPPrincipal(unittest.TestCase):
    """Tests for _get_ldap_principal."""

    def test_returns_users_entry_for_user_type(self):
        """getattr(plugin, 'users')[id] returned for type='users' (lines 66-67)."""
        sheet, mock_ldap_principal = _make_bare_sheet(principal_type="users")
        result = sheet._get_ldap_principal()
        sheet._plugin.users.__getitem__.assert_called_with("uid0")
        self.assertIs(result, mock_ldap_principal)

    def test_returns_groups_entry_for_group_type(self):
        """getattr(plugin, 'groups')[id] returned for type='groups' (lines 66-67)."""
        sheet, mock_ldap_principal = _make_bare_sheet(principal_type="groups")
        result = sheet._get_ldap_principal()
        sheet._plugin.groups.__getitem__.assert_called_with("uid0")
        self.assertIs(result, mock_ldap_principal)


# ---------------------------------------------------------------------------
# canWriteProperty  (line 71)
# ---------------------------------------------------------------------------

class TestCanWriteProperty(unittest.TestCase):
    """Tests for canWriteProperty."""

    def test_returns_true_for_existing_property(self):
        """Returns True when id is in _properties (line 71)."""
        sheet, _ = _make_bare_sheet(properties={"mail": "test@example.com"})
        self.assertTrue(sheet.canWriteProperty(None, "mail"))

    def test_returns_false_for_nonexistent_property(self):
        """Returns False when id is NOT in _properties (line 71)."""
        sheet, _ = _make_bare_sheet(properties={"mail": "test@example.com"})
        self.assertFalse(sheet.canWriteProperty(None, "cn"))


# ---------------------------------------------------------------------------
# setProperty  (lines 73-82)
# ---------------------------------------------------------------------------

class TestSetProperty(unittest.TestCase):
    """Tests for setProperty."""

    def test_updates_properties_dict(self):
        """_properties[id] is updated with the new value (line 77)."""
        sheet, _ = _make_bare_sheet(properties={"mail": "old@example.com"})
        sheet.setProperty(None, "mail", "new@example.com")
        self.assertEqual(sheet._properties["mail"], "new@example.com")

    def test_updates_ldap_attrs(self):
        """ldapprincipal.attrs[id] is updated (line 77)."""
        sheet, mock_ldap_principal = _make_bare_sheet(properties={"mail": "old@example.com"})
        sheet.setProperty(None, "mail", "new@example.com")
        mock_ldap_principal.attrs.__setitem__.assert_called_with("mail", "new@example.com")

    def test_calls_ldapprincipal_context(self):
        """ldapprincipal.context() is called to persist the change (line 79)."""
        sheet, mock_ldap_principal = _make_bare_sheet(properties={"mail": "old@example.com"})
        sheet.setProperty(None, "mail", "new@example.com")
        mock_ldap_principal.context.assert_called_once()

    def test_logs_error_on_context_exception(self):
        """Exception from context() is caught and logged (lines 80-82)."""
        sheet, _ = _make_bare_sheet(
            properties={"mail": "old@example.com"}, context_raises=True
        )
        with patch("pas.plugins.ldap.sheet.logger") as mock_logger:
            sheet.setProperty(None, "mail", "new@example.com")
        mock_logger.error.assert_called_once()
        msg = mock_logger.error.call_args[0][0]
        self.assertIn("ctx_error", msg)

    def test_asserts_id_must_be_in_properties(self):
        """setProperty raises AssertionError for an unknown property (line 75)."""
        sheet, _ = _make_bare_sheet(properties={"mail": "old@example.com"})
        with self.assertRaises(AssertionError):
            sheet.setProperty(None, "nonexistent", "value")


# ---------------------------------------------------------------------------
# setProperties  (lines 84-95)
# ---------------------------------------------------------------------------

class TestSetProperties(unittest.TestCase):
    """Tests for setProperties."""

    def test_updates_all_properties(self):
        """All properties in mapping are updated (lines 89-90)."""
        sheet, _ = _make_bare_sheet(properties={"mail": "old@example.com", "cn": "Old"})
        sheet.setProperties(None, {"mail": "new@example.com", "cn": "New"})
        self.assertEqual(sheet._properties["mail"], "new@example.com")
        self.assertEqual(sheet._properties["cn"], "New")

    def test_updates_ldap_attrs_for_all_keys(self):
        """ldapprincipal.attrs[id] is set for each key in mapping (line 90)."""
        sheet, mock_ldap_principal = _make_bare_sheet(
            properties={"mail": "old@example.com", "cn": "Old"}
        )
        sheet.setProperties(None, {"mail": "new@example.com", "cn": "New"})
        calls = mock_ldap_principal.attrs.__setitem__.call_args_list
        call_keys = {c[0][0] for c in calls}
        self.assertIn("mail", call_keys)
        self.assertIn("cn", call_keys)

    def test_calls_ldapprincipal_context(self):
        """ldapprincipal.context() is called once to persist all changes (line 92)."""
        sheet, mock_ldap_principal = _make_bare_sheet(
            properties={"mail": "old@example.com"}
        )
        sheet.setProperties(None, {"mail": "new@example.com"})
        mock_ldap_principal.context.assert_called_once()

    def test_logs_error_on_context_exception(self):
        """Exception from context() is caught and logged (lines 93-95)."""
        sheet, _ = _make_bare_sheet(
            properties={"mail": "old@example.com"}, context_raises=True
        )
        with patch("pas.plugins.ldap.sheet.logger") as mock_logger:
            sheet.setProperties(None, {"mail": "new@example.com"})
        mock_logger.error.assert_called_once()
        msg = mock_logger.error.call_args[0][0]
        self.assertIn("ctx_error", msg)

    def test_asserts_all_ids_must_be_in_properties(self):
        """setProperties raises AssertionError for an unknown property (line 87)."""
        sheet, _ = _make_bare_sheet(properties={"mail": "old@example.com"})
        with self.assertRaises(AssertionError):
            sheet.setProperties(None, {"nonexistent": "value"})

    def test_asserts_checks_all_keys_before_updating(self):
        """Validation loop (lines 86-87) runs before update loop (lines 89-90)."""
        sheet, mock_ldap_principal = _make_bare_sheet(
            properties={"mail": "old@example.com"}
        )
        with self.assertRaises(AssertionError):
            sheet.setProperties(None, {"mail": "new@example.com", "bad_key": "value"})
        # ldapprincipal.context() must NOT have been called (failed before update)
        mock_ldap_principal.context.assert_not_called()
