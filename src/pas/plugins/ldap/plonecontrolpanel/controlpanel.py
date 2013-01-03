# -*- coding: utf-8 -*-
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory
from Products.CMFCore.interfaces import ISiteRoot
from Products.statusmessages.interfaces import IStatusMessage
from pas.plugins.ldap.properties import BasePropertiesForm


_ = MessageFactory('pas.plugins.ldap')


def getPortal():
    return getUtility(ISiteRoot)


class LDAPControlPanel(BasePropertiesForm):

    def next(self, request):
        return '%s/plone_ldapcontrolpanel' % self.context.absolute_url()

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
        messages.addStatusMessage(_(u'LDAP Settings saved.'), type="info")
