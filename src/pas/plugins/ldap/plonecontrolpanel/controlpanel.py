# -*- coding: utf-8 -*-
from pas.plugins.ldap.properties import BasePropertiesForm
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
        super(LDAPControlPanel, self).__init__(context, request)
        add_bundle_on_request(request, "yafowil")

    def next(self, request):
        return "%s/plone_ldapcontrolpanel" % self.context.absolute_url()

    @property
    def plugin(self):
        """ControlPanel config is only for GS installed 'pasldap' plugin
        """
        portal = getPortal()
        aclu = portal.acl_users
        plugin = aclu.pasldap
        return plugin

    def save(self, widget, data):
        BasePropertiesForm.save(self, widget, data)
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"LDAP Settings saved."), type="info")
