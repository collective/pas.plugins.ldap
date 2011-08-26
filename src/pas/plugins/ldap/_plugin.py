import os
import ldap
import logging
from zope.interface import implements
from zope.component import getUtility
from zope.globalrequest import getRequest
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from node.ext.ldap.ugm import Ugm
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.interfaces import ISiteRoot
from Products.PluggableAuthService.permissions import (
    ManageUsers,
    ManageGroups,
)
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PlonePAS import interfaces as plonepas_interfaces
from .sheet import LDAPUserPropertySheet
from .interfaces import ILDAPPlugin 

logger = logging.getLogger('pas.plugins.ldap')

zmidir = os.path.join(os.path.dirname( __file__), 'zmi')

def manage_addLDAPPlugin(dispatcher, id, title='',  RESPONSE=None, **kw):
    """Create an instance of a LDAP Plugin.
    """
    ldapplugin = LDAPPlugin(id, title, **kw)
    dispatcher._setObject(ldapplugin.getId(), ldapplugin)
    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addLDAPPluginForm = PageTemplateFile(
    os.path.join(zmidir, 'add_plugin.pt'),
    globals(),
    __name__='addLDAPPlugin'
)

class LDAPPlugin(BasePlugin):
    """Glue layer for making node.ext.ldap available to PAS.
    """
    security = ClassSecurityInfo()
    meta_type = 'LDAP Plugin'    
    
    implements(
        ILDAPPlugin,
        pas_interfaces.IAuthenticationPlugin,
        pas_interfaces.IGroupEnumerationPlugin,
        pas_interfaces.IGroupsPlugin,
        pas_interfaces.IPropertiesPlugin,
        pas_interfaces.IUserEnumerationPlugin,
        plonepas_interfaces.capabilities.IDeleteCapability,
        plonepas_interfaces.capabilities.IGroupCapability,
        plonepas_interfaces.capabilities.IPasswordSetCapability,
        plonepas_interfaces.group.IGroupManagement,
        plonepas_interfaces.plugins.IMutablePropertiesPlugin,
        plonepas_interfaces.plugins.IUserManagement,
        )

    manage_options = ( 
        { 'label' : 'LDAP Settings',
          'action' : 'manage_ldapplugin'
        },) + BasePlugin.manage_options 
        
    #XXX: turn this to False when going productive, just in case
    _dont_swallow_my_exceptions = True # Tell PAS not to swallow our exceptions    

    def __init__(self, id, title=None, **kw):
        self._setId(id)
        self.title = title

    security.declarePrivate('groups_enabled')
    @property
    def groups_enabled(self):
        return self.groups is not None

    security.declarePrivate('users_enabled')
    @property
    def users_enabled(self):
        return self.users is not None

    def _ugm(self):
        request = getRequest()
        if not request:
            print "request is None !?"
        rcachekey = '_ldap_ugm_%s_' % self.getId()
        if request and rcachekey in request.keys():
            return request[rcachekey]
        props = ILDAPProps(self)
        ucfg = ILDAPUsersConfig(self)
        gcfg = ILDAPGroupsConfig(self)
        ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=None)
        if request:
            request[rcachekey] = ugm
        return ugm
    
    security.declarePrivate('groups')
    @property
    def groups(self):
        try:
            self._v_ldaperror = False
            return self._ugm().groups
        except ldap.LDAPError, e:
            self._v_ldaperror = str(e)
            logger.warn('groups -> %s' % self._v_ldaperror)
            return None
        except Exception, e: 
            self._v_ldaperror = str(e)
            logger.exception('groups -> %s' % self._v_ldaperror)
            return None

    security.declarePrivate('users')
    @property
    def users(self):
        try:
            self._v_ldaperror = False
            return self._ugm().users
        except ldap.LDAPError, e:
            self._v_ldaperror = str(e)
            logger.warn('groups -> %s' % self._v_ldaperror)
            return None
        except Exception, e: 
            self._v_ldaperror = str(e)
            logger.exception('groups -> %s' % self._v_ldaperror)
            return None
        
    security.declareProtected(ManageUsers, 'ldaperror')
    @property
    def ldaperror(self):
        if hasattr(self, '_v_ldaperror') and self._v_ldaperror:
            return self._v_ldaperror
        return False

    security.declarePublic('reset')
    def reset(self):
        # XXX flush caches
        pass

    ###
    # pas_interfaces.IAuthenticationPlugin
    #
    #  Map credentials to a user ID.
    #
    def authenticateCredentials(self, credentials):
        """credentials -> (userid, login)

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """
        login = credentials.get('login')
        pw = credentials.get('password')
        if not (login and pw):
            return None
        logger.debug('credentials: %s' % credentials)
        users = self.users
        if not users:
            return
        userid = users.authenticate(login, pw)
        if userid:
            logger.info('logged in %s' % userid)
            return (userid, login)

    ###
    # pas_interfaces.IGroupEnumerationPlugin
    #
    #  Allow querying groups by ID, and searching for groups.
    #    o XXX:  can these be done by a single plugin?
    #
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
        if id:
            kw['id'] = id
        groups = self.groups
        if not groups:
            logger.warn(self._v_ldaperror)
            return []
        try:
            matches = groups.search(criteria=kw, exact_match=exact_match)
        except ValueError:
            return ()
        pluginid = self.getId()
        ret = [
            dict(id=id.encode('ascii', 'replace'), pluginid=pluginid)
            for id in matches
            ]
        if max_results and len(ret) > max_results:
            ret = ret[:max_results]
        return ret

    ###
    # pas_interfaces.IGroupsPlugin
    #
    #  Determine the groups to which a user belongs.
    def getGroupsForPrincipal(self, principal, request=None):
        """principal -> ( group_1, ... group_N )

        o Return a sequence of group names to which the principal
          (either a user or another group) belongs.

        o May assign groups based on values in the REQUEST object, if present
        """
        users = self.users
        if not users:
            return tuple()
        try:
            _principal = self.users[principal.getId()]
        except KeyError:
            # XXX: that's where group in group will happen, but so far
            # group nodes do not provide membership info so we just
            # return if there is no user
            return tuple()
        if self.groups: 
            return [_.id for _ in _principal.groups]
        return tuple()

    ###
    # pas_interfaces.IUserEnumerationPlugin
    #
    #   Allow querying users by ID, and searching for users.
    #    o XXX:  can these be done by a single plugin?
    #
    def enumerateUsers(self, id=None, login=None, exact_match=False,
            sort_by=None, max_results=None, **kw):
        """-> ( user_info_1, ... user_info_N )

        o Return mappings for users matching the given criteria.

        o 'id' or 'login', in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).

        o If 'exact_match' is False, then 'id' and / or login may be
          treated by the plugin as "contains" searches (more complicated
          searches may be supported by some plugins using other keyword
          arguments).

        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' and 'login' (some plugins may support
          others).

        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all users satisfying the criteria.

        o Minimal keys in the returned mappings:

          'id' -- (required) the user ID, which may be different than
                  the login name

          'login' -- (required) the login name

          'pluginid' -- (required) the plugin ID (as returned by getId())

          'editurl' -- (optional) the URL to a page for updating the
                       mapping's user

        o Plugin *must* ignore unknown criteria.

        o Plugin may raise ValueError for invalid criteria.

        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        """
        # TODO: sort_by in node.ext.ldap
        if id:
            kw['id'] = id
        if login:
            kw['login'] = login
        users = self.users
        if not users:
            return tuple()
        try:
            matches = users.search(
                criteria=kw,
                attrlist=('login',),
                exact_match=exact_match
            )
        except ValueError:
            return ()
        pluginid = self.getId()
        ret = [dict(
            id=id.encode('ascii', 'replace'),
            login=attrs['login'][0], #XXX: see node.ext.ldap.users.Users.search
            pluginid=pluginid,
            ) for id, attrs in matches]
        if max_results and len(ret) > max_results:
            ret = ret[:max_results] 
        return ret

    ###
    # plonepas_interfaces.group.IGroupManagement
    #
    def addGroup(self, id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        return True if the operation suceeded
        """
        #XXX
        return False

    def addPrincipalToGroup(self, principal_id, group_id):
        """
        Add a given principal to the group.
        return True on success
        """
        #XXX
        return False

    def updateGroup(self, id, **kw):
        """
        Edit the given group. plugin specific
        return True on success
        """
        #XXX
        return False

    def setRolesForGroup(self, group_id, roles=()):
        """
        set roles for group
        return True on success
        """
        # even Products.PlonePAS.plugins.GroupAwareRoleManager does not 
        # implement this. We're save to ignore it too for now. But at least
        # we do implement it. 
        return False

    def removeGroup(self, group_id):
        """
        Remove the given group
        return True on success
        """
        #XXX
        return False

    def removePrincipalFromGroup(self, principal_id, group_id):
        """
        remove the given principal from the group
        return True on success
        """
        #XXX
        return False

    ###
    # plonepas_interfaces.plugins.IMutablePropertiesPlugin
    # (including signature of pas_interfaces.IPropertiesPlugin)
    #
    #  Return a property set for a user. Property set can either an object
    #  conforming to the IMutable property sheet interface or a dictionary (in
    #  which case the properties are not persistently mutable).
    #
    def getPropertiesForUser(self, user_or_group, request=None):
        """User -> IMutablePropertySheet || {}

        o User will implement IPropertiedUser. ???

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present
        """
        ugid = user_or_group.getId()
        if self.enumerateUsers(id=ugid):
            return LDAPUserPropertySheet(user_or_group, self)
        if self.enumerateGroups(id=ugid):
            return LDAPUserPropertySheet(user_or_group, self)
        return {}

    def setPropertiesForUser(self, user, propertysheet):
        """Set modified properties on the user persistently.

        Does nothing, it is called by MutablePropertySheet in
        setProperty and setProperties. This should not affect us at
        all as we handle setting of properties via our own
        LDAPPropertySheet
        """
        pass

    def deleteUser(self, user_id):
        """Remove properties stored for a user.

        Does nothing, if a user is deleted by ``doDeleteUser``, all it's
        properties are away as well.
        """
        pass

    ###
    # plonepas_interfaces.plugins.IUserManagement
    # (including signature of pas_interfaces.IUserAdderPlugin)
    #
    def doAddUser(self, login, password):
        """ Add a user record to a User Manager, with the given login
            and password

        o Return a Boolean indicating whether a user was added or not
        """
        # XXX
        return False

    def doChangeUser(self, user_id, password, **kw):
        """Change a user's password (differs from role) roles are set in
        the pas engine api for the same but are set via a role
        manager)
        """
        users = self.users
        if self.users:
            self.users.passwd(user_id, None, password)

    def doDeleteUser(self, login):
        """Remove a user record from a User Manager, with the given login
        and password

        o Return a Boolean indicating whether a user was removed or
          not
        """
        # XXX
        return False

    ###
    # plonepas_interfaces.capabilities.IDeleteCapability
    # (plone ui specific)
    #
    def allowDeletePrincipal(self, id):
        """True if this plugin can delete a certain user/group.
        """
        # XXX
        return False

    ###
    # plonepas_interfaces.capabilities.IGroupCapability
    # (plone ui specific)
    #
    def allowGroupAdd(self, principal_id, group_id):
        """
        True if this plugin will allow adding a certain principal to
        a certain group.
        """
        # XXX
        return False

    def allowGroupRemove(self, principal_id, group_id):
        """
        True if this plugin will allow removing a certain principal
        from a certain group.
        """
        # XXX
        return False

    ###
    # plonepas_interfaces.capabilities.IPasswordSetCapability
    # (plone ui specific)
    #
    def allowPasswordSet(self, id):
        """True if this plugin can set the password of a certain user.
        """
        users = self.users
        if not users:
            return False
        try:
            return len(self.users.search(criteria={'id': id},
                                         attrlist=(),
                                         exact_match=True)) > 0
        except ValueError:
            return False
        
InitializeClass(LDAPPlugin)