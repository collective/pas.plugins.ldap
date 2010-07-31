# Copyright (c) 2006-2009 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

import logging
logger = logging.getLogger('PASGroupsFromLDAP')

import socket, os
import types
from sets import Set
from Acquisition import Implicit, aq_parent, aq_base, aq_inner
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from Globals import InitializeClass
from Globals import package_home
from OFS.Cache import Cacheable
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.utils import createViewName
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.permissions import ManageGroups
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PluggableAuthService.interfaces.plugins import (
    IGroupsPlugin,
    IGroupEnumerationPlugin,
    IRolesPlugin,
    IPropertiesPlugin,
)
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PlonePAS.plugins.group import PloneGroup
from zope.interface import Interface, implements

from bda.ldap.properties import LDAPServerProperties
from bda.ldap.session import LDAPSession
from bda.ldap.base import BASE, ONELEVEL, SUBTREE

ALLOWED_SCOPES = {'BASE': BASE, 'ONELEVEL': ONELEVEL, 'SUBTREE': SUBTREE}

_wwwdir = os.path.join( package_home( globals() ), 'www' )

manage_addGroupsFromLDAPMultiPluginForm = PageTemplateFile(
    os.path.join(_wwwdir, 'addGroupsFromLDAPMultiPlugin'),
    globals(),
    __name__='addGroupsFromLDAPMultiPlugin')

def manage_addGroupsFromLDAPMultiPlugin(self, id, title, server, port,
                                        managerdn, password, groupdn, scope,
                                        objectclasses, escapevalues,
                                        attributeid, attributetitle,
                                        attributemembers, 
                                        attributegroupattr=None, 
                                        REQUEST=None):
    """Factory method to instantiate a GroupsFromLDAPMultiPlugin.
    """
    # Make sure we really are working in our container (the
    # PluggableAuthService object.
    self = self.this()

    # Instantiate the folderish adapter object
    plugin = GroupsFromLDAPMultiPlugin(id, title=title)
    self._setObject(id, plugin)
    
    if REQUEST is None:
        req = {
            'form': {
                'server': server,
                'port': port,
                'managerdn': managerdn,
                'password': password,
                'groupdn': groupdn,
                'scope': scope,
                'objectclasses': objectclasses,
                'escapevalues': escapevalues,
                'attributeid': attributeid,
                'attributetitle': attributetitle,
                'attributemembers': attributemembers,
                'attributegroupattr': attributegroupattr,
            },
        }
    else:
        req = REQUEST
    plugin.manage_changeConfiguration(req, fromadd=True)
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect('%s/manage_main' % self.absolute_url())
    
class IGroupsFromLDAPMultiPlugin(Interface):
    """Marker Interface"""

class GroupsFromLDAPMultiPlugin(BasePlugin, Cacheable):
    ''' fetches group info from LDAP and provides in PAS'''

    security = ClassSecurityInfo()

    implements(IGroupsFromLDAPMultiPlugin)

    __implements__ = (getattr(BasePlugin,'__implements__',()),)

    meta_type = 'GroupsFromLDAPMultiPlugin'

    config_whitelist=['server','port','managerdn','password',
                      'groupdn','scope','objectclasses','escapevalues',
                      'attributeid','attributetitle','attributemembers',
                      'attributegroupattr',]

    def __init__(self, id, title=None):
        self.id = id
        self.title = title
        self.config = {}
        # common configuration for ldap connection
        self.config['server'] = 'localhost'
        self.config['port'] = '389'
        self.config['managerdn'] = ''
        self.config['password'] = ''

        # ActiveDirectory value-escaping
        self.config['escapevalues'] = False

        # group specific ldap configuration
        self.config['groupdn'] = ''
        self.config['scope'] = 'ONELEVEL'
        self.config['objectclasses'] = ['posixGroup']
        self.config['attributeid'] = 'cn'
        self.config['attributemembers'] = 'memberUid'
        self.config['attributetitle'] = 'cn'
        self.config['attributegroupattr'] = ''
        self.initializeLDAP()

    #---------------------------------------------------------------------------
    # (Plone)PAS interface defined methods

    # implements interface IGroupsPlugin (PAS)
    def getGroupsForPrincipal(self, principal, request=None ):
        """ principal -> ( group_1, ... group_N )

        o Return a sequence of group names to which the principal
          (either a user or another group) belongs.

        o May assign groups based on values in the REQUEST object, if present
          (optional, you also can ignore it)
        """
        userid = principal.getUserId()
        groupattr = self.config.get('attributegroupattr',None)
        if groupattr:
            plugins = self.acl_users._getOb('plugins')
            propfinders = plugins.listPlugins(IPropertiesPlugin)
            id_for_group = None 
            for propfinder in propfinders:
                ps = propfinder[1].getPropertiesForUser(principal)
                if ps:
                    if hasattr(ps,'get'):
                        id_for_group = ps.get(groupattr)
                    elif hasattr(ps,'getProperty'):
                        id_for_group = ps.getProperty(groupattr)
                if id_for_group:
                    userid = id_for_group #.decode('Latin1').encode('utf-8')
                    break

        result = self.searchGroupsOfUser(self.config['groupdn'],
                                         self.config['attributeid'],
                                         self.config['attributemembers'],
                                         userid,
                                         ALLOWED_SCOPES[self.config['scope']],
                                         objectClass=self.config['objectclasses'])
        return tuple(result)

    # implements interface IGroupEnumeration (PAS)
    def enumerateGroups(self, id=None, exact_match=False, sort_by=None,
                        max_results=None, **kw):

        """ -> ( group_info_1, ... group_info_N )

        o Return mappings for groups matching the given criteria.

        o 'id' in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).

        o If 'exact_match' is False, then 'id' may be treated by
          the plugin as "contains" searches (more complicated searches
          may be supported by some plugins using other keyword arguments).

        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' (some plugins may support others).

        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all groups satisfying the
          criteria.

        o Minimal keys in the returned mappings:

          'id' -- (required) the group ID

          'pluginid' -- (required) the plugin ID (as returned by getId())

          'properties_url' -- (optional) the URL to a page for updating the
                              group's properties.

          'members_url' -- (optional) the URL to a page for updating the
                           principals who belong to the group.

        o Plugin *must* ignore unknown criteria.

        o Plugin may raise ValueError for invalid critera.

        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        """

        if id is None:
            search = '*'
        elif not exact_match:
            search = '*%s*' % id
        else:
            search = id

        res = self.searchGroups(self.config['groupdn'],
                                self.config['attributeid'],
                                ALLOWED_SCOPES[self.config['scope']],
                                search=search,
                                objectClass=self.config['objectclasses'])
        ret = []
        # TODO: implement max_results
        for id in res:
            ret.append({'id': id, 'pluginid': self.id})
        return ret

    # implements interface IGroupIntrospection (PlonePAS)
    def getGroupById(self, groupid, default=None):
        """
        Returns the portal_groupdata-ish object for a group
        corresponding to this id.
        """
        plugins = self.acl_users._getOb('plugins')
        group = self.makeGroup(plugins, groupid, title=None, request=None)
        if group is None:
            return default
        return group

    # implements interface IGroupIntrospection (PlonePAS)
    def getGroups(self):
        """
        Returns an iteration of the available groups
        """
        return map(self.getGroupById, self.getGroupIds())

    # implements interface IGroupIntrospection (PlonePAS)
    def getGroupIds(self):
        """
        Returns a list of the available groups
        """
        return [e['id'] for e in  self.enumerateGroups()]

    # implements interface IGroupIntrospection (PlonePAS)
    def getGroupMembers(self, groupid):
        """
        return the members of the given group
        """
        res = self.searchMembersOfGroup(self.config['groupdn'],
                                        self.config['attributeid'],
                                        self.config['attributemembers'],
                                        groupid,
                                        ALLOWED_SCOPES[self.config['scope']],
                                        objectClass=self.config['objectclasses'])
        return res

    # implements interface IPropertiesPlugin (PAS)
    def getPropertiesForUser(self, group, request=None ):

        """ group -> {}

        o Group will implement IPropertiedUser.
        """
        groupid = group.getId()
        result = self.searchGroups(self.config['groupdn'],
                                   self.config['attributeid'],
                                   ALLOWED_SCOPES[self.config['scope']],
                                   groupid,
                                   objectClass=self.config['objectclasses'],
                                   titleattr=self.config['attributetitle'],
                                   )
        # check if theres a group with that id
        if len(result) == 0:
            return None
        id, gtitle = result[0]
        if not gtitle:
            return None
        ps = UserPropertySheet(self.id, title=gtitle)
        return ps

    # implements interface IRolesPlugin (PAS)
    def getRolesForPrincipal(self, principal, request=None):
        """ principal -> ( group_1, ... group_N )

        o Return a sequence of group names to which the principal
          (either a user or another group) belongs.

        o Deals only with the groups roles.


        """
        plugins = self.acl_users._getOb('plugins')
        groupids = self.getGroupsForPrincipal(principal, request)
        roles = Set()
        for gid in groupids:
            rolemakers = plugins.listPlugins(IRolesPlugin)
            for rolemaker_id, rolemaker in rolemakers:
                if rolemaker_id == self.getId():
                    continue
                group = self.makeGroup(plugins, gid)
                foundroles = rolemaker.getRolesForPrincipal(group, request)
                if foundroles:
                    roles.update(foundroles)
        return tuple(roles)


    #---------------------------------------------------------------------------
    # convinience methods
    security.declarePrivate('searchGroups')
    def searchGroups(self, basedn, groupattr, scope, search='*',
                     objectClass=[], titleattr=None):
        """Search for groups in LDAP Directory.

        Take the base DN, the group attribute name, a valid scope from 
        bda.ldap.base, and optional a searchstring, a list of objectClass names 
        and a title attribute defining in which field the group name is stored. 
        If titleattr is given, return a list of tuples containing (id, title) 
        of the groups, otherwise return a list of ids.
        """
        view_name = createViewName('GroupsFromLDAPMultiPlugin.searchGroups', 
                                   self.id)
        keywords = { 'key': '='.join([str(basedn), str(groupattr), str(scope),
                                      str(search), str(objectClass),
                                      str(titleattr)])
        }
        cached = self.ZCacheable_get(view_name=view_name,
                                     keywords=keywords,
                                     default=None)
        if cached is not None:
            return cached

        self.ldap.setBaseDN(basedn)

        query = '(&(%s=%s)' % (groupattr, self.escapeValue(search))
        for oc in objectClass:
            query = '%s(objectClass=%s)' % (query, oc)
        query = '%s)' % query
        
        try:
            res = self.ldap.search(query, scope)
        except Exception, ex:
            logger.warn('ldap search failed in searchGroups')
            logger.warn('query: %s' % query)
            logger.warn('error: %s' % ex)
            return []

        ret = []
        for rec in res:
            if titleattr is None:
                ret.append(rec[1].get(groupattr)[0])
            else:
                ret.append((rec[1].get(groupattr)[0], rec[1].get(titleattr, 
                                                                 [None])[0]))

        self.ZCacheable_set(ret, view_name=view_name, keywords=keywords)
        return ret

    security.declarePrivate('searchGroupsOfUser')
    def searchGroupsOfUser(self, basedn, groupattr, userattr, uservalue,
                           scope, objectClass=[]):
        """Search for the groups a user is member of.

        Take the base DN, the group attribute name, the user attibute name used 
        in groups, the user value to search for, a valid scope from 
        bda.ldap.base and optional a list of objectClass names. 
        Return a list of group ids.
        """
        view_name = createViewName('GroupsFromLDAPMultiPlugin.searchGroupsOfUser', 
                                   self.id)
        keywords = {'key': '='.join([str(basedn), str(groupattr), str(userattr),
                                     str(uservalue), str(scope), 
                                     str(objectClass)])}

        cached = self.ZCacheable_get(view_name=view_name,
                                     keywords=keywords,
                                     default=None)
        if cached is not None:
            return cached

        self.ldap.setBaseDN(basedn)

        query = '(&(%s=*)' % groupattr
        for oc in objectClass:
            query = '%s(objectClass=%s)' % (query, oc)
        query = '%s(%s=%s)' % (query, userattr, self.escapeValue(uservalue))
        query = '%s)' % query

        try:
            res = self.ldap.search(query, scope)
        except Exception, ex:
            logger.warn('ldap search failed in searchGroupsOfUser')
            logger.warn('query: %s' % query)
            logger.warn('error: %s' % ex)
            return []

        ret = []
        for rec in res:
            ret.append(rec[1].get(groupattr)[0])

        self.ZCacheable_set(ret, view_name=view_name, keywords=keywords)
        return ret

    security.declarePrivate('searchMembersOfGroup')
    def searchMembersOfGroup(self, basedn, groupattr, userattr, groupvalue, 
                             scope, objectClass=[]):
        """Search for the members of a group

        Take the base DN, the group attribute name, the user attibute name used 
        in groups, the group value to search for, a valid scope from 
        bda.ldap.base and optional a list of objectClass names. 
        Returns a list of member ids.
        """
        view_name = createViewName('GroupsFromLDAPMultiPlugin.searchMembersOfGroup', 
                                   self.id)
        keywords = {'key': '&'.join([basedn, groupattr, userattr, groupvalue,
                                     str(scope), str(objectClass)])}

        cached = self.ZCacheable_get(view_name=view_name,
                                     keywords=keywords,
                                     default=None)
        if cached is not None:
            return cached

        self.ldap.setBaseDN(basedn)

        query = '(&(%s=%s)' % (groupattr, self.escapeValue(groupvalue))
        for oc in objectClass:
            query = '%s(objectClass=%s)' % (query, oc)
        query = '%s(%s=*)' % (query, userattr)
        query = '%s)' % query

        try:
            res = self.ldap.search(query, scope)
        except Exception, ex:
            logger.warn('ldap search failed in searchMembersOfGroup')
            logger.warn('query: %s' % query)
            logger.warn('error: %s' % ex)
            return []

        if len(res) > 0:
            ret = res[0][1].get(userattr)
        else:
            ret = []
        self.ZCacheable_set(ret, view_name=view_name, keywords=keywords)
        return ret

    security.declarePrivate('makeGroup')
    def makeGroup(self, plugins, groupid, title=None, request=None):
        """ group_id -> decorated_group
        This method based on PluggableAuthService._findGroup
        """

        # See if the group can be retrieved from the cache
        view_name = createViewName('GroupsFromLDAPMultiPlugin.makeGroup', 
                                   self.id)
        keywords = { 'group_id' : groupid,

                     'title' : title
                   }
        group = self.ZCacheable_get(view_name=view_name
                                  , keywords=keywords
                                  , default=None
                                 )
        if group is not None:
            # cache hit
            group = group.__of__(self)
            return group

        # verify group and its title from LDAP
        result = self.searchGroups(self.config['groupdn'],
                                   self.config['attributeid'],
                                   ALLOWED_SCOPES[self.config['scope']],
                                   groupid,
                                   objectClass=self.config['objectclasses'],
                                  )
        # check if theres a group with that id
        if len(result) == 0:
            return None

        # check if for some reason the wrong group was returned.
        # this must never happen
        if result[0] != groupid:
            raise ValueError, 'Group with id '+\
                  '"%s" expected, but LDAP returned record with id "%s"' % \
                  (groupid, id)

        # create the plone style group object
        group = PloneGroup(groupid)

        # acquisition-wrapper
        group = group.__of__(self)

        # add UserPropertySheet with title
        propfinders = plugins.listPlugins(IPropertiesPlugin)
        for propfinder_id, propfinder in propfinders:

            data = propfinder.getPropertiesForUser(group, request)
            if data:
                group.addPropertysheet(propfinder_id, data)

        # fetch and set groups our group is part of
        groups = self.acl_users._getGroupsForPrincipal(group, request,
                                                       plugins=plugins)
        group._addGroups(groups)

        # fetch and set roles
        rolemakers = plugins.listPlugins(IRolesPlugin)
        for rolemaker_id, rolemaker in rolemakers:
            roles = rolemaker.getRolesForPrincipal(group, request)
            if roles:
                group._addRoles(roles)
        group._addRoles(['Authenticated'])

        # Cache the group if caching is enabled
        base_group = aq_base(group)
        if getattr(base_group, '_p_jar', None) is None:
            self.ZCacheable_set(base_group,
                                view_name=view_name,
                                keywords=keywords,
                              )
        return group


    #---------------------------------------------------------------------------
    # helper methods
    def escapeValue(self, query):
        """ Escapes a query, note that this is documented for AD queries, but 
            not for OpenLDAP etc; But hopefully they work in the same manner.
        """
        config = self.getConfig()
        if not config['escapevalues']:
            return query
        replacements = {'(' :'\\28',
                        ')' :'\\29',
                        '\\':'\\5c',
                        '/' :'\\2f',
                        }
                        # don't know how to 'find' NUL = \\0
                        #'*' :'\\2a',
        for key, value in replacements.items():
            query = query.replace(key, value)
        return query
    
    #---------------------------------------------------------------------------
    # administrative methods
    security.declarePrivate('initializeLDAP')
    def initializeLDAP(self):
        try:
            port = int(self.config['port'])
        except ValueError:
            logger.warn('')
            port = self.config['port'] = 389
        ldapserverprops = LDAPServerProperties(self.config['server'],
                                               port,
                                               self.config['managerdn'],
                                               self.config['password'])
        self._v_ldap = LDAPSession(ldapserverprops)
    
    @property
    def ldap(self):
        if not hasattr(self, '_v_ldap') or not self._v_ldap:
            self.initializeLDAP()
        return self._v_ldap

    security.declareProtected( ManageGroups, 'getConfig' )
    def getConfig(self):
        # start migration code
        if self.config.get('escapevalues', None) is None:
            self.config['escapevalues'] = False
        # end migration code

        return self.config

    security.declareProtected( ManageGroups, 'checkServerProperties' )
    def checkServerProperties(self):
        state, message = self.ldap.checkServerProperties()
        return state, message

    security.declareProtected( ManageGroups, 'manage_changeConfiguration' )
    def manage_changeConfiguration(self, REQUEST=None, fromadd=False):
        """ manages submitted form """
        if not REQUEST:
            return
        if hasattr(REQUEST, 'form'):
            form = REQUEST.form
        else:
            # case adding from setuphandler
            form = REQUEST['form']
        for key in form.keys():
            if key in self.config_whitelist:
                self.config[key] = form.get(key)
                # special list handling
                if key == 'objectclasses':
                    self.config[key] = [c.strip() for c in \
                                        self.config[key].split(',')]
                if key == 'scope' \
                   and self.config[key] not in ALLOWED_SCOPES.keys():
                    self.config[key] = ALLOWED_SCOPES.keys()[2]
                if key == 'escapevalues':
                    self.config[key] = self.config[key] == 'yes'
        self._p_changed = 1
        self.initializeLDAP()
        if fromadd:
            return
        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         '/manage_LDAPBaseDNs')

    security.declareProtected( ManageGroups, 'manage_LDAPBaseDNs' )
    manage_LDAPBaseDNs = PageTemplateFile(
        os.path.join(_wwwdir, 'manage_base_dns'),
        globals(),
        __name__='manage_LDAPBaseDNs')

    manage_options =  ( { 'label' : 'LDAP Base DNs'
                        , 'action' : 'manage_LDAPBaseDNs'
                        }
                      ,
                      ) + BasePlugin.manage_options + Cacheable.manage_options

classImplements(GroupsFromLDAPMultiPlugin, IGroupsPlugin,
                                           IGroupEnumerationPlugin,
                                           IGroupIntrospection,
                                           IPropertiesPlugin,
                                           IRolesPlugin)
InitializeClass(GroupsFromLDAPMultiPlugin)
