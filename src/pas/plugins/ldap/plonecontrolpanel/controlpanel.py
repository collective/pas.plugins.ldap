from ..properties import BasePropertiesForm
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.resources import add_bundle_on_request
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory


_ = MessageFactory("pas.plugins.ldap")


def getPortal():
    return getUtility(ISiteRoot)


class LDAPControlPanel(BasePropertiesForm):
    def __init__(self, context, request):
        super().__init__(context, request)
        add_bundle_on_request(request, "yafowil")

    def next(self, request):
        return f"{self.context.absolute_url()}/plone_ldapcontrolpanel"

    @property
    def plugin(self):
        """ControlPanel config is only for GS installed 'pasldap' plugin"""
        portal = getPortal()
        aclu = portal.acl_users
        return aclu.pasldap

    def save(self, widget, data):
        super().save(widget, data)
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_("LDAP Settings saved."), type="info")
