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
            

class PropsBase(object):

    def __init__(self, context):
        self.context = context
        self.strict = False

    @property
    def propsheet(self):
        properties = getPortal().portal_properties
        return properties.restrictedTraverse(self.sheetname)

    @property
    def sheetname(self):
        raise NotImplementedError(u"Abstract Properties does not implement"
                                  u"``sheetname``")

    def _set(self, name, val):
        if isinstance(val, odict):
            val = json.dumps(val.items())
        sheet = self.propsheet
        if sheet.hasProperty(name):
            sheet._updateProperty(name, val)
        else:
            sheet._setProperty(name, val)

    def _get(self, name):
        return self.propsheet.getProperty(name)
           
class LDAPProps(PropsBase):

    implements(ILDAPProps)
    adapts(IPloneSiteRoot)

    @property
    def sheetname(self):
        return 'ldap_properties'

    def _get_uri(self):
        return self._get('uri')

    def _set_uri(self, val):
        self._set('uri', val)

    uri = property(_get_uri, _set_uri)

    def _get_user(self):
        return self._get('user')

    def _set_user(self, val):
        self._set('user', val)

    user = property(_get_user, _set_user)

    def _get_password(self):
        return self._get('password')

    def _set_password(self, val):
        self._set('password', val)

    password = property(_get_password, _set_password)

    def _get_cache(self):
        return self._get('cache')

    def _set_cache(self, val):
        self._set('cache', val)

    cache = property(_get_cache, _set_cache)

    def _get_timeout(self):
        return self._get('timeout')

    def _set_timeout(self, val):
        self._set('timeout', val)

    timeout = property(_get_timeout, _set_timeout)

    def _get_start_tls(self):
        return self._get('start_tls')

    def _set_start_tls(self, val):
        self._set('start_tls', val)

    start_tls = property(_get_start_tls, _set_start_tls)

    def _get_tls_cacertfile(self):
        return self._get('tls_cacertfile')

    def _set_tls_cacertfile(self, val):
        self._set('tls_cacertfile', val)

    tls_cacertfile = property(_get_tls_cacertfile, _set_tls_cacertfile)

    def _get_tls_cacertdir(self):
        return self._get('tls_cacertdir')

    def _set_tls_cacertdir(self, val):
        self._set('tls_cacertdir', val)

    tls_cacertdir = property(_get_tls_cacertdir, _set_tls_cacertdir)

    def _get_tls_clcertfile(self):
        return self._get('tls_clcertfile')

    def _set_tls_clcertfile(self, val):
        self._set('tls_clcertfile', val)

    tls_clcertfile = property(_get_tls_clcertfile, _set_tls_clcertfile)

    def _get_tls_clkeyfile(self):
        return self._get('tls_clkeyfile')

    def _set_tls_clkeyfile(self, val):
        self._set('tls_clkeyfile', val)

    tls_clkeyfile = property(_get_tls_clkeyfile, _set_tls_clkeyfile)

    def _get_retry_max(self):
        return self._get('retry_max')

    def _set_retry_max(self, val):
        self._set('retry_max', val)

    retry_max = property(_get_retry_max, _set_retry_max)

    def _get_retry_delay(self):
        return self._get('retry_delay')

    def _set_retry_delay(self, val):
        self._set('retry_delay', val)

    retry_delay = property(_get_retry_delay, _set_retry_delay)

class LDAPPrincipalsConfig(PropsBase):

    def _get_baseDN(self):
        return self._get('baseDN')

    def _set_baseDN(self, val):
        self._set('baseDN', val)

    baseDN = property(_get_baseDN, _set_baseDN)

    def _get_attrmap(self):
        val = self._get('attrmap')
        if val is None:
            return odict()
        val = json.loads(val)
        val = odict(val)
        return val

    def _set_attrmap(self, val):
        self._set('attrmap', val)

    attrmap = property(_get_attrmap, _set_attrmap)

    def _get_scope(self):
        return self._get('scope')

    def _set_scope(self, val):
        self._set('scope', val)

    scope = property(_get_scope, _set_scope)

    def _get_queryFilter(self):
        return self._get('queryFilter')

    def _set_queryFilter(self, val):
        self._set('queryFilter', val)

    queryFilter = property(_get_queryFilter, _set_queryFilter)

    def _get_objectClasses(self):
        val = self._get('objectClasses')
        if not val:
            return list()
        return json.loads(val)

    def _set_objectClasses(self, val):
        self._set('objectClasses', json.dumps(val))

    objectClasses = property(_get_objectClasses, _set_objectClasses)

class LDAPUsersConfig(LDAPPrincipalsConfig):

    implements(ILDAPUsersConfig)
    adapts(IPloneSiteRoot)

    @property
    def sheetname(self):
        return 'ldap_users_config'

class LDAPGroupsConfig(LDAPPrincipalsConfig):

    implements(ILDAPGroupsConfig)
    adapts(IPloneSiteRoot)

    @property
    def sheetname(self):
        return 'ldap_groups_config'
