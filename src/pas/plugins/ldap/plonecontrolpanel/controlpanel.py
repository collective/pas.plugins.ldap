"""Control panel for LDAP plugin"""

from ..properties import BasePropertiesForm
from pas.plugins.ldap import _
from plumber import plumbing
from Products.statusmessages.interfaces import IStatusMessage
from yafowil.plone.form import CSRFProtectionBehavior
from zope.component.hooks import getSite


@plumbing(CSRFProtectionBehavior)
class LDAPControlPanel(BasePropertiesForm):
    """Control panel for managing LDAP settings."""

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
        portal = getSite()
        aclu = portal.acl_users
        # Use direct item access to avoid Zope acquisition walking up the
        # chain when 'pasldap' is not installed, which produces a misleading
        # "'RequestContainer' object has no attribute 'pasldap'" error.
        try:
            return aclu["pasldap"]
        except KeyError:
            raise AttributeError(
                "Plugin 'pasldap' not found in acl_users. "
                "Install pas.plugins.ldap via Plone Add-ons first."
            )

    def save(self, widget, data):
        """Save the LDAP setting.

        Args:
            widget (Widget): Widget instance
            data (Data): Data extracted from the form
        """
        super().save(widget, data)
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_("LDAP Settings saved."), type="info")
