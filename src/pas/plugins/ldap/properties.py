import os
import json
import ldap
import logging
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
from zope.component import adapts
import transaction
import yafowil.zope2
from yafowil.base import UNSET
from yafowil.controller import Controller
from yafowil.yaml import parse_from_YAML
from zope.i18nmessageid import MessageFactory
from persistent.dict import PersistentDict
from zExceptions import Redirect
from Products.Five import BrowserView
from .interfaces import ILDAPPlugin

logger = logging.getLogger('pas.plugins.ldap')

_ = MessageFactory('pas.plugins.ldap')


class BasePropertiesForm(BrowserView):
    
    yaml = os.path.join(os.path.dirname(__file__), 'properties.yaml')

    scope_vocab = [
        (str(BASE), 'BASE'),
        (str(ONELEVEL), 'ONELEVEL'),
        (str(SUBTREE), 'SUBTREE'),
    ]
    
    static_attrs = ['rdn', 'id', 'login']

    @property
    def plugin(self):
        raise NotImplementedError()

    def next(self, request):
        raise NotImplementedError()

    @property
    def action(self):
        return self.next({}) 


    def form(self):
        # make configuration data available on form context
        self.props =  ILDAPProps(self.plugin)
        self.users =  ILDAPUsersConfig(self.plugin)
        self.groups = ILDAPGroupsConfig(self.plugin)

        # prepare users data on form context
        self.users_attrmap = odict()
        for key in self.static_attrs:
            self.users_attrmap[key] = self.users.attrmap.get(key)
        
        self.users_propsheet_attrmap = odict()
        for key, value in self.users.attrmap.items():
            if key in self.static_attrs:
                continue
            self.users_propsheet_attrmap[key] = value

        # prepare groups data on form context
        self.groups_attrmap = odict()
        for key in self.static_attrs:
            self.groups_attrmap[key] = self.groups.attrmap.get(key)
        self.groups_propsheet_attrmap = odict()
        for key, value in self.groups.attrmap.items():
            if key in self.static_attrs:
                continue
            self.groups_propsheet_attrmap[key] = value

        # handle form
        form = parse_from_YAML(self.yaml, self,  _)
        controller = Controller(form, self.request)
        if not controller.next:
            return controller.rendered
        raise Redirect(controller.next)    

    
    def save(self, widget, data):
        props =  ILDAPProps(self.plugin)
        users =  ILDAPUsersConfig(self.plugin)
        groups = ILDAPGroupsConfig(self.plugin)
        def fetch(name):
            name = 'ldapsettings.%s' % name
            __traceback_info__ = name
            return data.fetch(name).extracted
        props.uri = fetch('server.uri')
        props.user = fetch('server.user')
        password = fetch('server.password')
        if password is not UNSET:
            props.password = password
        props.cache = fetch('server.cache')
        props.memcached = fetch('server.memcached')
        props.timeout = fetch('server.timeout')
        # XXX: later
        #props.start_tls = fetch('server.start_tls')
        #props.tls_cacertfile = fetch('server.tls_cacertfile')
        #props.tls_cacertdir = fetch('server.tls_cacertdir')
        #props.tls_clcertfile = fetch('server.tls_clcertfile')
        #props.tls_clkeyfile = fetch('server.tls_clkeyfile')
        #props.retry_max = fetch(at('server.retry_max')
        #props.retry_delay = fetch('server.retry_delay')
        users.baseDN = fetch('users.dn')
        map = odict()
        map.update(fetch('users.aliases_attrmap'))
        users_propsheet_attrmap = fetch('users.propsheet_attrmap')
        if users_propsheet_attrmap is not UNSET:
            map.update(users_propsheet_attrmap)
        users.attrmap = map
        users.scope = fetch('users.scope')
        users.queryFilter = fetch('users.query')
        objectClasses = fetch('users.object_classes')
        objectClasses = \
            [v.strip() for v in objectClasses.split(',') if v.strip()]
        users.objectClasses = objectClasses
        groups = self.groups
        groups.baseDN = fetch('groups.dn')
        map = odict()
        map.update(fetch('groups.aliases_attrmap'))
        groups_propsheet_attrmap = fetch('groups.propsheet_attrmap')
        if groups_propsheet_attrmap is not UNSET:
            map.update(groups_propsheet_attrmap)
        groups.attrmap = map
        groups.scope = fetch('groups.scope')
        groups.queryFilter = fetch('groups.query')
        objectClasses = fetch('groups.object_classes')
        objectClasses = \
            [v.strip() for v in objectClasses.split(',') if v.strip()]
        groups.objectClasses = objectClasses       
        
    def connection_test(self):
        props =  ILDAPProps(self.plugin)
        users =  ILDAPUsersConfig(self.plugin)
        groups = ILDAPGroupsConfig(self.plugin)
        ugm = Ugm('test', props=props, ucfg=users, gcfg=groups)
        try:
            ugm.users
        except ldap.SERVER_DOWN, e:
            return False, _("Server Down")
        except ldap.LDAPError, e:
            return False, _('LDAP users; ') + str(e)
        except Exception, e:
            logger.exception('Non-LDAP error while connection test!')
            return False, _('Other; ') + str(e)
        try:
            ugm.groups
        except ldap.LDAPError, e:
            return False, _('LDAP Users ok, but groups not; ') + \
                   e.message['desc']
        except Exception, e:
            logger.exception('Non-LDAP error while connection test!')
            return False, _('Other; ') + str(e)
        return True, 'Connection, users- and groups-access tested successfully.'         
                    
DEFAULTS = {
    'server.uri'          : 'ldap://127.0.0.1:12345',
    'server.user'         :  'cn=Manager,dc=my-domain,dc=com',
    'server.password'     :  'secret',
    'server.cache'        :  False,
    'server.memcached'    :  '127.0.0.1:11211',
    'server.timeout'      :  300,
    'server.start_tls'    :  False,
            
    'users.baseDN'        : 'ou=users300,dc=my-domain,dc=com',
    'users.attrmap'       : '{"rdn": "uid", "id": "uid", "login": "uid",'\
                            ' "fullname": "cn", "email": "mail"}',
    'users.scope'         : '1',
    'users.queryFilter'   : '(objectClass=inetOrgPerson)',
    'users.objectClasses' : '["inetOrgPerson"]',
    
    'groups.baseDN'       : 'ou=groups,dc=my-domain,dc=com',
    'groups.attrmap'      : '{"rdn": "uid", "id": "uid", "login": "uid",'\
                            ' "fullname": "cn", "email": "mail"}',
    'groups.scope'        : '1',
    'groups.queryFilter'  : '(objectClass=groupOfNames)',
    'groups.objectClasses': '["groupOfNames"]',
}

def propproxy(ckey, usejson=False):
    def _getter(context):
        value = context.plugin.settings.get(ckey, DEFAULTS[ckey])
        if usejson:
            value = json.loads(value)
        return value
    def _setter(context, value):
        if usejson:
            value = json.dumps(value)
        context.plugin.settings[ckey] = value
        transaction.commit() # XXX: needed here, why? otherwise no persistence        
    return property(_getter, _setter)


class LDAPProps(object):

    implements(ILDAPProps)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin

    uri = propproxy('server.uri')
    user = propproxy('server.user')
    password = propproxy('server.password')
    cache = propproxy('server.cache')
    memcached = propproxy('server.memcached')
    timeout = propproxy('server.timeout')
    
    # XXX: Later
    start_tls = propproxy('server.start_tls')
    tls_cacertfile = ''
    tls_cacertdir = ''
    tls_clcertfile = ''
    tls_clkeyfile = ''
    retry_max = 3
    retry_delay = 5    
    

class UsersConfig(object):

    implements(ILDAPUsersConfig)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin
        
    strict = False

    baseDN = propproxy('users.baseDN')
    attrmap = propproxy('users.attrmap', True)
    scope = propproxy('users.scope', True)
    queryFilter = propproxy('users.queryFilter') 
    objectClasses = propproxy('users.objectClasses', True)

    
class GroupsConfig(object):

    implements(ILDAPGroupsConfig)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin

    strict = False

    baseDN = propproxy('groups.baseDN')
    attrmap = propproxy('groups.attrmap', True)
    scope = propproxy('groups.scope', True)
    queryFilter = propproxy('groups.queryFilter') 
    objectClasses = propproxy('groups.objectClasses', True)