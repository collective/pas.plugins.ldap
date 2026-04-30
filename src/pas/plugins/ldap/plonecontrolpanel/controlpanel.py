"""Control panel for LDAP plugin"""

from ..properties import BasePropertiesForm
from pas.plugins.ldap import _
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.resources import add_bundle_on_request
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getUtility


def getPortal():
    """Get the Plone portal object."""
    return getUtility(ISiteRoot)


class LDAPControlPanel(BasePropertiesForm):
    """Control panel for managing LDAP settings."""

    def __init__(self, context, request):
        super().__init__(context, request)
        add_bundle_on_request(request, "yafowil")

    def next(self, request):
        """Next

        Args:
            request (object): Request object

        Returns:
            str: Absolute URL String
        """
        return f"{self.context.absolute_url()}/plone_ldapcontrolpanel"

    @property
    def plugin(self):
        """ControlPanel config is only for GS installed 'pasldap' plugin"""
        portal = getPortal()
        aclu = portal.acl_users
        return aclu.pasldap

    def save(self, widget, data):
        """Save the LDAP setting.

        Args:
            widget (Widget): Widget instance
            data (Data): Data extracted from the form
        """
        super().save(widget, data)
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_("LDAP Settings saved."), type="info")
