# -*- coding: utf-8 -*-
import os
import transaction
import ldap
try:
    import json
except ImportError:
    import simplejson as json
from odict import odict
from node.ext.ldap.scope import (
    BASE,
    ONELEVEL,
    SUBTREE,
)
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from node.ext.ldap.ugm import Ugm
from zope.interface import implements
from zope.component import (
    adapts,
    getUtility,
)
from zope.i18nmessageid import MessageFactory
from Products.Five import BrowserView
from yafowil.base import UNSET
from yafowil.controller import Controller
from yafowil.yaml import parse_from_YAML
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect

_ = MessageFactory('pas.plugins.ldap')

def getPortal():
    return getUtility(ISiteRoot)

class LDAPControlPanel(BrowserView):
    
    yaml = os.path.join(os.path.dirname(__file__), 'controlpanel.yaml')

    scope_vocab = [
        (str(BASE), 'BASE'),
        (str(ONELEVEL), 'ONELEVEL'),
        (str(SUBTREE), 'SUBTREE'),
    ]
    
    static_attrs = ['rdn', 'id', 'login']

    def form(self):
        # prepare users data
        self.users_attrmap = odict()
        for key in self.static_attrs:
            self.users_attrmap[key] = self.users.attrmap.get(key)
        
        self.users_propsheet_attrmap = odict()
        for key, value in self.users.attrmap.items():
            if key in self.static_attrs:
                continue
            self.users_propsheet_attrmap[key] = value

        # prepare groups data
        self.groups_attrmap = odict()
        for key in self.static_attrs:
            self.groups_attrmap[key] = self.groups.attrmap.get(key)
        self.groups_propsheet_attrmap = odict()
        for key, value in self.groups.attrmap.items():
            if key in self.static_attrs:
                continue
            self.groups_propsheet_attrmap[key] = value

        form = parse_from_YAML(self.yaml, self,  _)
        controller = Controller(form, self.request)
        if not controller.next:
            return controller.rendered
        raise Redirect(controller.next)

    def save(self, widget, data):
        props = self.props
        fetch = data.fetch
        def at(name):
            return 'ldapsettings.%s' % name
        props.uri = data.fetch(at('server.uri')).extracted
        props.user = data.fetch(at('server.user')).extracted
        password = data.fetch(at('server.password')).extracted
        if password is not UNSET:
            props.password = password
        # XXX: later
        #props.cache = fetch(at('cache')).extracted
        #props.timeout = fetch(at('timeout')).extracted
        #props.start_tls = fetch(at('start_tls')).extracted
        #props.tls_cacertfile = fetch(at('tls_cacertfile')).extracted
        #props.tls_cacertdir = fetch(at('tls_cacertdir')).extracted
        #props.tls_clcertfile = fetch(at('tls_clcertfile')).extracted
        #props.tls_clkeyfile = fetch(at('tls_clkeyfile')).extracted
        #props.retry_max = fetch(at('retry_max')).extracted
        #props.retry_delay = fetch(at('retry_delay')).extracted
        users = self.users
        users.baseDN = fetch(at('users.dn')).extracted
        map = odict()
        map.update(fetch(at('users.aliases_attrmap')).extracted)
        users_propsheet_attrmap = fetch(at('users.propsheet_attrmap')).extracted
        if users_propsheet_attrmap is not UNSET:
            map.update(users_propsheet_attrmap)
        users.attrmap = map
        users.scope = fetch(at('users.scope')).extracted
        users.queryFilter = fetch(at('users.query')).extracted
        objectClasses = fetch(at('users.object_classes')).extracted
        objectClasses = \
            [v.strip() for v in objectClasses.split(',') if v.strip()]
        users.objectClasses = objectClasses
        groups = self.groups
        groups.baseDN = fetch(at('groups.dn')).extracted
        map = odict()
        map.update(fetch(at('groups.aliases_attrmap')).extracted)
        groups_propsheet_attrmap = fetch(at('groups.propsheet_attrmap')).extracted
        if groups_propsheet_attrmap is not UNSET:
            map.update(groups_propsheet_attrmap)
        groups.attrmap = map
        groups.scope = fetch(at('groups.scope')).extracted
        groups.queryFilter = fetch(at('groups.query')).extracted
        objectClasses = fetch(at('groups.object_classes')).extracted
        objectClasses = \
            [v.strip() for v in objectClasses.split(',') if v.strip()]
        groups.objectClasses = objectClasses
        # getLDAPPlugin().reset()
        # XXX send event notify here
        transaction.commit() #XXX?
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u'LDAP Settings saved.'), type="info")
        
    def next(self, request):
        # XXX. set status message
        return '%s/@@ldap-controlpanel' % self.context.absolute_url()

    @property
    def props(self):
        return ILDAPProps(getPortal())

    @property
    def users(self):
        return ILDAPUsersConfig(getPortal())

    @property
    def groups(self):
        return ILDAPGroupsConfig(getPortal())
    
    def connection_test(self):
        ugm = Ugm('test', props=self.props, ucfg=self.users, gcfg=self.groups)
        try:
            ugm.users
        except ldap.SERVER_DOWN, e:
            return False, _("Server Down")
        except ldap.LDAPError, e:
            return False, _('LDAP Error (users): ') + e.message['desc']
        try:
            ugm.groups
        except ldap.LDAPError, e:
            return False, _('LDAP Error (groups): ') + e.message['desc']
        return True, 'OK'