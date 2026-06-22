"""Pure unit tests for pas.plugins.ldap.monkey module.

100% coverage without Zope/LDAP layer.
"""

import unittest
from unittest.mock import MagicMock, call, patch

from pas.plugins.ldap.monkey import (
    PortraitImage,
    PortraitTraverser,
    getPortraitFromSheet,
    patched_getPersonalPortrait,
)


# ---------------------------------------------------------------------------
# PortraitImage.getPhysicalPath  (lines 22-26)
# ---------------------------------------------------------------------------


class TestPortraitImageGetPhysicalPath(unittest.TestCase):
    """Tests for PortraitImage.getPhysicalPath."""

    def _make_portrait(self, img_id="uid0"):
        """Create PortraitImage bypassing OFS.Image.__init__."""
        portrait = PortraitImage.__new__(PortraitImage)
        # In Zope, self.id() is called as a method in getPhysicalPath.
        # Use a callable mock so the f-string works.
        portrait.id = MagicMock(return_value=img_id)
        return portrait

    def test_parent_with_getphysicalpath_appends_traversal(self):
        """When parent has getPhysicalPath, returns combined path (line 26)."""
        portrait = self._make_portrait("uid0")
        mock_parent = MagicMock()
        mock_parent.getPhysicalPath.return_value = ("", "plone", "acl_users")
        with patch("pas.plugins.ldap.monkey.aq_inner", return_value=portrait), \
             patch("pas.plugins.ldap.monkey.aq_parent", return_value=mock_parent):
            result = portrait.getPhysicalPath()
        self.assertEqual(result, ("", "plone", "acl_users", "++portrait++uid0"))

    def test_parent_without_getphysicalpath_returns_root_trav(self):
        """When parent has no getPhysicalPath, returns ('', trav) (line 25)."""
        portrait = self._make_portrait("uid0")
        mock_parent = object()  # plain object, no getPhysicalPath attr
        with patch("pas.plugins.ldap.monkey.aq_inner", return_value=portrait), \
             patch("pas.plugins.ldap.monkey.aq_parent", return_value=mock_parent):
            result = portrait.getPhysicalPath()
        self.assertEqual(result, ("", "++portrait++uid0"))


# ---------------------------------------------------------------------------
# getPortraitFromSheet  (lines 31-50)
# ---------------------------------------------------------------------------


class TestGetPortraitFromSheet(unittest.TestCase):
    """Tests for getPortraitFromSheet."""

    def _member_not_found(self):
        """Return mock mtool that resolves no member."""
        mtool = MagicMock()
        mtool.getMemberById.return_value = None
        return mtool

    def _member_with_sheet(self, property_ids, portrait_data=None, fullname="Test User"):
        """Return (mtool, mock_user) for a member with one property sheet."""
        mock_sheet = MagicMock()
        mock_sheet.propertyIds.return_value = property_ids
        if portrait_data is not None:
            mock_sheet.getProperty.return_value = portrait_data

        mock_user = MagicMock()
        mock_user.listPropertysheets.return_value = ["ldap"]
        mock_user.getPropertysheet.return_value = mock_sheet
        mock_user.getProperty.return_value = fullname

        mock_member = MagicMock()
        mock_member.getUser.return_value = mock_user

        mtool = MagicMock()
        mtool.getMemberById.return_value = mock_member
        return mtool, mock_user

    # --- branch: member not found ---

    def test_returns_none_when_member_not_found(self):
        """getMemberById returns falsy → return None (line 34)."""
        context = MagicMock()
        with patch("pas.plugins.ldap.monkey.getToolByName",
                   return_value=self._member_not_found()):
            result = getPortraitFromSheet(context, "uid0")
        self.assertIsNone(result)

    # --- branch: no portrait in sheets ---

    def test_returns_none_when_no_sheets(self):
        """User has no property sheets → return None (line 44)."""
        context = MagicMock()
        mock_user = MagicMock()
        mock_user.listPropertysheets.return_value = []
        mock_member = MagicMock()
        mock_member.getUser.return_value = mock_user
        mtool = MagicMock()
        mtool.getMemberById.return_value = mock_member
        with patch("pas.plugins.ldap.monkey.getToolByName", return_value=mtool):
            result = getPortraitFromSheet(context, "uid0")
        self.assertIsNone(result)

    def test_returns_none_when_sheet_has_no_portrait_property(self):
        """Sheet exists but no 'portrait' in propertyIds → return None (line 44)."""
        context = MagicMock()
        mtool, _ = self._member_with_sheet(["email", "fullname"])
        with patch("pas.plugins.ldap.monkey.getToolByName", return_value=mtool):
            result = getPortraitFromSheet(context, "uid0")
        self.assertIsNone(result)

    # --- branch: portrait found ---

    def test_returns_portrait_image_when_portrait_in_sheet(self):
        """Portrait found in sheet → returns PortraitImage (line 50)."""
        context = MagicMock()
        mtool, _ = self._member_with_sheet(
            property_ids=["portrait"],
            portrait_data=b"JPEG_DATA",
            fullname="Full Name",
        )
        mock_portrait_img = MagicMock()
        with patch("pas.plugins.ldap.monkey.getToolByName", return_value=mtool), \
             patch("pas.plugins.ldap.monkey.PortraitImage",
                   return_value=mock_portrait_img), \
             patch("pas.plugins.ldap.monkey.BytesIO"):
            result = getPortraitFromSheet(context, "uid0")
        self.assertIs(result, mock_portrait_img)

    def test_portrait_image_created_with_correct_args(self):
        """PortraitImage is constructed with userid, fullname, sio, content_type."""
        context = MagicMock()
        mtool, mock_user = self._member_with_sheet(
            property_ids=["portrait"],
            portrait_data=b"DATA",
            fullname="Jane Doe",
        )
        mock_sio = MagicMock()
        with patch("pas.plugins.ldap.monkey.getToolByName", return_value=mtool), \
             patch("pas.plugins.ldap.monkey.PortraitImage") as MockPI, \
             patch("pas.plugins.ldap.monkey.BytesIO", return_value=mock_sio):
            getPortraitFromSheet(context, "testuser")

        MockPI.assert_called_once_with("testuser", "Jane Doe", mock_sio, "image/jpeg")
        mock_sio.write.assert_called_once_with(b"DATA")


# ---------------------------------------------------------------------------
# PortraitTraverser  (lines 58-59, 63)
# ---------------------------------------------------------------------------


class TestPortraitTraverser(unittest.TestCase):
    """Tests for PortraitTraverser.__init__ and traverse."""

    def test_init_stores_context_and_request(self):
        """__init__ stores context and request (lines 58-59)."""
        ctx = MagicMock()
        req = MagicMock()
        traverser = PortraitTraverser(ctx, req)
        self.assertIs(traverser.context, ctx)
        self.assertIs(traverser.request, req)

    def test_init_request_defaults_to_none(self):
        """request parameter defaults to None when omitted."""
        ctx = MagicMock()
        traverser = PortraitTraverser(ctx)
        self.assertIsNone(traverser.request)

    def test_traverse_calls_getPortraitFromSheet_and_of(self):
        """traverse calls getPortraitFromSheet(context, userid).__of__(context) (line 63)."""
        ctx = MagicMock()
        traverser = PortraitTraverser(ctx)

        # __of__ is an Acquisition method — MagicMock raises AttributeError for it
        # because it matches the "dunder" pattern.  Use a simple stub instead.
        mock_wrapped = MagicMock()
        of_calls = []

        class _PortraitStub:
            def __of__(self, context):
                of_calls.append(context)
                return mock_wrapped

        mock_portrait = _PortraitStub()

        with patch(
            "pas.plugins.ldap.monkey.getPortraitFromSheet",
            return_value=mock_portrait,
        ) as mock_gp:
            result = traverser.traverse("uid0", [])

        mock_gp.assert_called_once_with(ctx, "uid0")
        self.assertEqual(of_calls, [ctx])
        self.assertIs(result, mock_wrapped)


# ---------------------------------------------------------------------------
# patched_getPersonalPortrait  (lines 72-94)
# ---------------------------------------------------------------------------


class TestPatchedGetPersonalPortrait(unittest.TestCase):
    """Tests for patched_getPersonalPortrait."""

    def _make_self(self):
        """Return a MagicMock that acts as MembershipTool instance."""
        return MagicMock()

    # --- userid resolution (lines 72-74) ---

    def test_uses_authenticated_member_id_when_id_is_none(self):
        """When id=None, userid comes from getAuthenticatedMember().getId() (line 74)."""
        mock_self = self._make_self()
        mock_self.getAuthenticatedMember.return_value.getId.return_value = "uid0"
        mock_portrait = MagicMock()
        with patch(
            "pas.plugins.ldap.monkey.getPortraitFromSheet",
            return_value=mock_portrait,
        ) as mock_gp:
            result = patched_getPersonalPortrait(mock_self, id=None)

        mock_self.getAuthenticatedMember.assert_called()
        mock_gp.assert_called_once_with(mock_self, "uid0")
        self.assertIs(result, mock_portrait)

    def test_uses_provided_id_directly(self):
        """When id is given, userid is set to it without calling getAuthenticatedMember."""
        mock_self = self._make_self()
        mock_portrait = MagicMock()
        with patch(
            "pas.plugins.ldap.monkey.getPortraitFromSheet",
            return_value=mock_portrait,
        ):
            patched_getPersonalPortrait(mock_self, id="uid1")

        mock_self.getAuthenticatedMember.assert_not_called()

    # --- portrait from sheet (lines 76-78) ---

    def test_returns_portrait_from_sheet_when_found(self):
        """If getPortraitFromSheet returns a portrait, return it immediately (line 78)."""
        mock_self = self._make_self()
        mock_portrait = MagicMock()
        with patch(
            "pas.plugins.ldap.monkey.getPortraitFromSheet",
            return_value=mock_portrait,
        ):
            result = patched_getPersonalPortrait(mock_self, id="uid0")

        self.assertIs(result, mock_portrait)

    # --- fallback to memberdata (lines 80-83) ---

    def test_falls_back_to_memberdata_when_no_sheet_portrait(self):
        """When sheet has no portrait, falls back to membertool._getPortrait (lines 81-83)."""
        mock_self = self._make_self()
        mock_portrait_obj = MagicMock()
        mock_membertool = MagicMock()
        mock_membertool._getPortrait.return_value = mock_portrait_obj

        with patch("pas.plugins.ldap.monkey.getPortraitFromSheet", return_value=None), \
             patch("pas.plugins.ldap.monkey.getToolByName",
                   return_value=mock_membertool):
            result = patched_getPersonalPortrait(mock_self, id="uid0")

        self.assertIs(result, mock_portrait_obj)

    # --- portrait is str → None (lines 84-85) ---

    def test_string_portrait_becomes_none_and_falls_back_to_portal(self):
        """_getPortrait returning a str → portrait=None → get default from portal (line 85)."""
        mock_self = self._make_self()
        mock_membertool = MagicMock()
        mock_membertool._getPortrait.return_value = "some_string"
        mock_portal = MagicMock()
        mock_portal_url_tool = MagicMock()
        mock_portal_url_tool.getPortalObject.return_value = mock_portal

        with patch("pas.plugins.ldap.monkey.getPortraitFromSheet", return_value=None), \
             patch(
                 "pas.plugins.ldap.monkey.getToolByName",
                 side_effect=[mock_membertool, mock_portal_url_tool],
             ), \
             patch("pas.plugins.ldap.monkey.default_portrait", "defaultUser.png"):
            result = patched_getPersonalPortrait(mock_self, id="uid0")

        mock_portal_url_tool.getPortalObject.assert_called_once()

    # --- verifyPermission branch (lines 86-89) ---

    def test_verify_permission_zero_skips_permission_check(self):
        """With verifyPermission=0 (default), _checkPermission is never called (line 87 skipped)."""
        mock_self = self._make_self()
        mock_portrait_obj = MagicMock()
        mock_membertool = MagicMock()
        mock_membertool._getPortrait.return_value = mock_portrait_obj

        with patch("pas.plugins.ldap.monkey.getPortraitFromSheet", return_value=None), \
             patch("pas.plugins.ldap.monkey.getToolByName",
                   return_value=mock_membertool), \
             patch("pas.plugins.ldap.monkey._checkPermission") as mock_check:
            result = patched_getPersonalPortrait(mock_self, id="uid0",
                                                 verifyPermission=0)

        mock_check.assert_not_called()
        self.assertIs(result, mock_portrait_obj)

    def test_verify_permission_denied_hides_portrait(self):
        """With verifyPermission=1, permission denied → portrait=None → default (lines 87-89)."""
        mock_self = self._make_self()
        mock_portrait_obj = MagicMock()
        mock_membertool = MagicMock()
        mock_membertool._getPortrait.return_value = mock_portrait_obj
        mock_portal = MagicMock()
        mock_portal_url_tool = MagicMock()
        mock_portal_url_tool.getPortalObject.return_value = mock_portal

        with patch("pas.plugins.ldap.monkey.getPortraitFromSheet", return_value=None), \
             patch(
                 "pas.plugins.ldap.monkey.getToolByName",
                 side_effect=[mock_membertool, mock_portal_url_tool],
             ), \
             patch("pas.plugins.ldap.monkey._checkPermission", return_value=False):
            result = patched_getPersonalPortrait(mock_self, id="uid0",
                                                 verifyPermission=1)

        mock_portal_url_tool.getPortalObject.assert_called_once()

    def test_verify_permission_granted_returns_portrait(self):
        """With verifyPermission=1, permission granted → portrait returned (line 94)."""
        mock_self = self._make_self()
        mock_portrait_obj = MagicMock()
        mock_membertool = MagicMock()
        mock_membertool._getPortrait.return_value = mock_portrait_obj

        with patch("pas.plugins.ldap.monkey.getPortraitFromSheet", return_value=None), \
             patch("pas.plugins.ldap.monkey.getToolByName",
                   return_value=mock_membertool), \
             patch("pas.plugins.ldap.monkey._checkPermission", return_value=True):
            result = patched_getPersonalPortrait(mock_self, id="uid0",
                                                 verifyPermission=1)

        self.assertIs(result, mock_portrait_obj)

    # --- fallback to portal default portrait (lines 90-92) ---

    def test_fallback_to_portal_default_when_portrait_is_none(self):
        """When portrait is None, gets default portrait from portal (lines 91-92)."""
        mock_self = self._make_self()
        mock_membertool = MagicMock()
        mock_membertool._getPortrait.return_value = None
        mock_default_portrait = MagicMock()
        mock_portal = MagicMock()
        setattr(mock_portal, "defaultUser.png", mock_default_portrait)
        mock_portal_url_tool = MagicMock()
        mock_portal_url_tool.getPortalObject.return_value = mock_portal

        with patch("pas.plugins.ldap.monkey.getPortraitFromSheet", return_value=None), \
             patch(
                 "pas.plugins.ldap.monkey.getToolByName",
                 side_effect=[mock_membertool, mock_portal_url_tool],
             ), \
             patch("pas.plugins.ldap.monkey.default_portrait", "defaultUser.png"):
            result = patched_getPersonalPortrait(mock_self, id="uid0")

        mock_portal_url_tool.getPortalObject.assert_called_once()
        self.assertIs(result, mock_default_portrait)


if __name__ == "__main__":
    unittest.main()
