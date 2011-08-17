import ldap
import logging
logger = logging.getLogger('bda.pasldap')

from zope.interface import implements
from zope.component import getUtility
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from node.ext.ldap.ugm import Ugm
from Products.CMFCore.interfaces import ISiteRoot
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PlonePAS import interfaces as plonepas_interfaces
from bda.pasldap.sheet import LDAPUserPropertySheet
from bda.pasldap.utils import (
    debug,
    if_groups_not_enabled_return,
    if_users_not_enabled_return,
)

# XXX
# comments in here are mostly taken from the corresponding interface
# declarations. Once we know what we are and are not going to support
# we could think about cleaning them up

class LDAPPlugin(BasePlugin, object):
    """Glue layer for making node.ext.ldap available to PAS.
    """
    implements(
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

    #XXX: turn this to False when going productive, just in case
    _dont_swallow_my_exceptions = True # Tell PAS not to swallow our exceptions
    meta_type = 'BDALDAPPlugin'

    def __init__(self, id, title=None):
        self.id = id
        self.title = title

    @property
    def groups_enabled(self):
        return self.groups is not None

    @property
    def users_enabled(self):
        return self.users is not None

    @property
    def ugm(self):
        if hasattr(self, '_v_ugm'):
            return self._v_ugm
        site = getUtility(ISiteRoot)
        props = ILDAPProps(site)
        ucfg = ILDAPUsersConfig(site)
        gcfg = ILDAPGroupsConfig(site)
        try:
            self._v_ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=None)
        except Exception, e:
            logger.error('caught: %s.' % str(e))
        return self._v_ugm
    
    @property
    def groups(self):
        if self.ugm:
            return self.ugm.groups

    @property
    def users(self):
        if self.ugm:
            return self.ugm.users

    def reset(self):
        delattr(self, '_v_ugm')

    ###
    # pas_interfaces.IAuthenticationPlugin
    #
    #  Map credentials to a user ID.
    #
    @if_users_not_enabled_return(None)
    @debug(['authentication'])
    def authenticateCredentials(self, credentials):
        """credentials -> (userid, login)

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """
        try:
            login = credentials['login']
            pw = credentials['password']
        except KeyError:
            # credentials were not meant for us
            return None
        uid = self.users.authenticate(login, pw)
        if uid:
            return (uid, login)

    ###
    # pas_interfaces.IGroupEnumerationPlugin
    #
    #  Allow querying groups by ID, and searching for groups.
    #    o XXX:  can these be done by a single plugin?
    #
    @if_groups_not_enabled_return(tuple())
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
        matches = self.groups.search(criteria=kw, exact_match=exact_match)
        pluginid = self.getId()
        ret = [
            dict(id=id.encode('ascii', 'replace'), pluginid=pluginid)
            for id in matches
            ]
        return ret

    ###
    # pas_interfaces.IGroupsPlugin
    #
    #  Determine the groups to which a user belongs.
    @if_groups_not_enabled_return(tuple())
    def getGroupsForPrincipal(self, principal, request=None):
        """principal -> ( group_1, ... group_N )

        o Return a sequence of group names to which the principal
          (either a user or another group) belongs.

        o May assign groups based on values in the REQUEST object, if present
        """
        try:
            _principal = self.users[principal.getId()]
        except KeyError:
            # XXX: that's where group in group will happen, but so far
            # group nodes do not provide membership info so we just
            # return if there is no user
            return tuple()
            try:
                _principal = self.groups[principal.getId()]
            except KeyError:
                return tuple()
        return _principal.groups.keys()

    ###
    # pas_interfaces.IUserEnumerationPlugin
    #
    #   Allow querying users by ID, and searching for users.
    #    o XXX:  can these be done by a single plugin?
    #
    @if_users_not_enabled_return(tuple())
    @debug(['userenumeration'])
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
        # TODO: max_results in node.ext.ldap
        # TODO: sort_by in node.ext.ldap
        if id:
            kw['id'] = id
        if login:
            kw['login'] = login
        matches = self.users.search(
            criteria=kw,
            attrlist=('login',),
            exact_match=exact_match
        )
        pluginid = self.getId()
        ret = [dict(
            id=id.encode('ascii', 'replace'),
            login=attrs['login'][0], #XXX: see node.ext.ldap.users.Users.search
            pluginid=pluginid,
            ) for id, attrs in matches]
        return ret

    ###
    # plonepas_interfaces.group.IGroupManagement
    #
    @if_groups_not_enabled_return(False)
    def addGroup(self, id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        return True if the operation suceeded
        """
        #XXX
        return False

    @if_groups_not_enabled_return(False)
    def addPrincipalToGroup(self, principal_id, group_id):
        """
        Add a given principal to the group.
        return True on success
        """
        #XXX
        return False

    @if_groups_not_enabled_return(False)
    def updateGroup(self, id, **kw):
        """
        Edit the given group. plugin specific
        return True on success
        """
        #XXX
        return False

    @if_groups_not_enabled_return(False)
    def setRolesForGroup(self, group_id, roles=()):
        """
        set roles for group
        return True on success
        """
        #XXX: should we? can we?
        return False

    @if_groups_not_enabled_return(False)
    def removeGroup(self, group_id):
        """
        Remove the given group
        return True on success
        """
        #XXX
        return False

    @if_groups_not_enabled_return(False)
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
    @if_users_not_enabled_return(dict())
    def getPropertiesForUser(self, user, request=None):
        """User -> IMutablePropertySheet || {}

        o User will implement IPropertiedUser. ???

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present
        """
        # XXX: this seems to be also called for groups - do something about it
        return LDAPUserPropertySheet(user, self)

    @if_users_not_enabled_return(None)
    def setPropertiesForUser(self, user, propertysheet):
        """Set modified properties on the user persistently.

        Does nothing, it is called by MutablePropertySheet in
        setProperty and setProperties. This should not affect us at
        all as we handle setting of properties via our own
        LDAPPropertySheet
        """
        pass

    @if_users_not_enabled_return(None)
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
    @if_users_not_enabled_return(False)
    def doAddUser(self, login, password):
        """ Add a user record to a User Manager, with the given login
            and password

        o Return a Boolean indicating whether a user was added or not
        """
        # XXX
        return False

    @if_users_not_enabled_return(False)
    def doChangeUser(self, login, password, **kw):
        """Change a user's password (differs from role) roles are set in
        the pas engine api for the same but are set via a role
        manager)
        """
        self.users.passwd(login, None, password)

    @if_users_not_enabled_return(False)
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
    @if_users_not_enabled_return(False)
    def allowDeletePrincipal(self, id):
        """True if this plugin can delete a certain user/group.
        """
        # XXX
        return False

    ###
    # plonepas_interfaces.capabilities.IGroupCapability
    # (plone ui specific)
    #
    @if_groups_not_enabled_return(False)
    def allowGroupAdd(self, principal_id, group_id):
        """
        True iff this plugin will allow adding a certain principal to
        a certain group.
        """
        # XXX
        return False

    @if_groups_not_enabled_return(False)
    def allowGroupRemove(self, principal_id, group_id):
        """
        True iff this plugin will allow removing a certain principal
        from a certain group.
        """
        # XXX
        return False

    ###
    # plonepas_interfaces.capabilities.IPasswordSetCapability
    # (plone ui specific)
    #
    @if_users_not_enabled_return(False)
    def allowPasswordSet(self, id):
        """True if this plugin can set the password of a certain user.
        """
        # XXX: should just be bool(self.get('id')), currently not because user
        # might be deleted and we don't know about
        return len(self.users.search(criteria={'id': id},
                                     attrlist=(),
                                     exact_match=True)) > 0
