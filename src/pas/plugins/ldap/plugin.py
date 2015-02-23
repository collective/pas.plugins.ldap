# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from BTrees import OOBTree
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PlonePAS import interfaces as plonepas_interfaces
from Products.PlonePAS.plugins.group import PloneGroup
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PluggableAuthService.permissions import ManageGroups
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from node.ext.ldap.base import decode_utf8
from node.ext.ldap.base import encode_utf8
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPProps
from node.ext.ldap.interfaces import ILDAPUsersConfig
from node.ext.ldap.ugm import Ugm
from pas.plugins.ldap.interfaces import ILDAPPlugin
from pas.plugins.ldap.sheet import LDAPUserPropertySheet
from plone.memoize import ram
from zope.interface import implementer
import ldap
import logging
import os
import time


logger = logging.getLogger('pas.plugins.ldap')
zmidir = os.path.join(os.path.dirname(__file__), 'zmi')

LDAP_ERROR_TIMEOUT = 300.0


def _ugm_cachekey(method, self):
    # TODO: settings seem not to work
    if not self.settings['cache.cache'] or not self.plugin_caching:
        # Return a always changing value to avoid caching
        return time.time()
    # Caching timeout in seconds, default is one hour.
    timeout = self.settings['cache.timeout'] or 60 * 60
    return (time.time() // timeout)


def manage_addLDAPPlugin(dispatcher, id, title='', RESPONSE=None, **kw):
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


def ldap_error_handler(prefix):
    """decorator, deals with non-working LDAP"""

    def _decorator(original_method):

        def _wrapper(self):
            # look if error is in timeout phase
            if hasattr(self, '_v_ldaperror_timeout'):
                waiting = time.time() - self._v_ldaperror_timeout
                if waiting < LDAP_ERROR_TIMEOUT:
                    logger.debug(
                        '{0}: retry wait {1:0.5f} of {2:0.0f}s -> {3}'.format(
                            prefix,
                            waiting,
                            LDAP_ERROR_TIMEOUT,
                            self._v_ldaperror_msg,
                        )
                    )
                    return None
            try:
                # call original method - get metrics
                start = time.clock()
                result = original_method(self)
                end = time.clock()
                logger.debug(
                    'call of {0!r} took {1:0.5f}s'.format(
                        original_method,
                        end - start
                    )
                )
                return result

            # handle errors
            except ldap.LDAPError, e:
                self._v_ldaperror_msg = str(e)
                self._v_ldaperror_timeout = time.time()
                logger.warn('LDAPError in {0} -> {1}'.format(prefix, str(e)))
                return None
            except Exception, e:
                self._v_ldaperror_msg = str(e)
                self._v_ldaperror_timeout = time.time()
                logger.warn('Error in {0} -> {1}'.format(prefix, str(e)))
                return None

        return _wrapper

    return _decorator


@implementer(
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
    plonepas_interfaces.group.IGroupIntrospection,
    plonepas_interfaces.plugins.IMutablePropertiesPlugin,
    plonepas_interfaces.plugins.IUserManagement)
class LDAPPlugin(BasePlugin):
    """Glue layer for making node.ext.ldap available to PAS.
    """
    security = ClassSecurityInfo()
    meta_type = 'LDAP Plugin'
    manage_options = ({
        'label': 'LDAP Settings',
        'action': 'manage_ldapplugin',
    }, ) + BasePlugin.manage_options

    # Tell PAS not to swallow our exceptions
    _dont_swallow_my_exceptions = False

    def __init__(self, id, title=None, **kw):
        self._setId(id)
        self.title = title
        self.settings = OOBTree.OOBTree()
        self.plugin_caching = True

    @property
    @security.private
    def groups_enabled(self):
        return self.groups is not None

    @property
    @security.private
    def users_enabled(self):
        return self.users is not None

    def _ugm(self):
        props = ILDAPProps(self)
        ucfg = ILDAPUsersConfig(self)
        gcfg = ILDAPGroupsConfig(self)
        ugm = Ugm(props=props, ucfg=ucfg, gcfg=gcfg, rcfg=None)
        return ugm

    @property
    @ldap_error_handler('groups')
    @security.private
    @ram.cache(_ugm_cachekey)
    def groups(self):
        return self._ugm().groups

    @property
    @ldap_error_handler('users')
    @security.private
    @ram.cache(_ugm_cachekey)
    def users(self):
        return self._ugm().users

    @property
    @security.protected(ManageUsers)
    def ldaperror(self):
        if hasattr(self, '_v_ldaperror_msg'):
            waiting = time.time() - self._v_ldaperror_timeout
            if waiting < LDAP_ERROR_TIMEOUT:
                return self._v_ldaperror_msg + ' (for %0.2fs)' % waiting
        return False

    @security.public  # really public??
    def reset(self):
        # XXX flush caches
        pass

    # ##
    # pas_interfaces.IAuthenticationPlugin
    #
    #  Map credentials to a user ID.
    #
    @security.public
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
            return None
        userid = users.authenticate(login, pw)
        if userid:
            logger.info('logged in %s' % userid)
            return (userid, login)
        return None

    # ##
    # pas_interfaces.IGroupEnumerationPlugin
    #
    #  Allow querying groups by ID, and searching for groups.
    #
    @security.private
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
        groups = self.groups
        if not groups:
            return ()
        if id:
            kw['id'] = id
        if not kw:  # show all
            matches = groups.ids
        else:
            try:
                matches = groups.search(criteria=kw, exact_match=exact_match)
            except ValueError:
                return ()
        if sort_by == 'id':
            matches = sorted(matches)
        pluginid = self.getId()
        ret = [dict(id=encode_utf8(_id), pluginid=pluginid) for _id in matches]
        if max_results and len(ret) > max_results:
            ret = ret[:max_results]
        return ret

    # ##
    # pas_interfaces.IGroupsPlugin
    #
    #  Determine the groups to which a user belongs.
    @security.private
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
            # XXX: provide group_ids function in UGM! Way too calculation-heavy
            #      now
            return [_.id for _ in _principal.groups]
        return tuple()

    # ##
    # pas_interfaces.IUserEnumerationPlugin
    #
    #   Allow querying users by ID, and searching for users.
    #
    @security.private
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
        if login:
            if not isinstance(login, basestring):
                # XXX TODO
                raise NotImplementedError('sequence is not supported yet.')
            kw['login'] = login

        # pas search users gives both login and name if login is meant
        if "login" in kw and "name" in kw:
            del kw["name"]

        if id:
            if not isinstance(id, basestring):
                # XXX TODO
                raise NotImplementedError('sequence is not supported yet.')
            kw['id'] = id
        users = self.users
        if not users:
            return tuple()
        try:
            matches = users.search(
                criteria=kw,
                attrlist=('login',),
                exact_match=exact_match)
        except ValueError:
            return tuple()
        pluginid = self.getId()
        ret = list()
        for id, attrs in matches:
            ret.append({
                'id': encode_utf8(id),
                'login': attrs['login'][0],
                'pluginid': pluginid})
        if max_results and len(ret) > max_results:
            ret = ret[:max_results]
        return ret

    # ##
    # plonepas_interfaces.group.IGroupManagement
    #
    @security.private
    def addGroup(self, id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        return True if the operation suceeded
        """
        # XXX
        return False

    @security.protected(ManageGroups)
    def addPrincipalToGroup(self, principal_id, group_id):
        """
        Add a given principal to the group.
        return True on success
        """
        # XXX
        return False

    @security.private
    def updateGroup(self, id, **kw):
        """
        Edit the given group. plugin specific
        return True on success
        """
        # XXX
        return False

    @security.private
    def setRolesForGroup(self, group_id, roles=()):
        """
        set roles for group
        return True on success
        """
        # even Products.PlonePAS.plugins.GroupAwareRoleManager does not
        # implement this. We're save to ignore it too for now. But at least
        # we do implement it.
        return False

    @security.private
    def removeGroup(self, group_id):
        """
        Remove the given group
        return True on success
        """
        # XXX
        return False

    @security.protected(ManageGroups)
    def removePrincipalFromGroup(self, principal_id, group_id):
        """
        remove the given principal from the group
        return True on success
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.plugins.IMutablePropertiesPlugin
    # (including signature of pas_interfaces.IPropertiesPlugin)
    #
    #  Return a property set for a user. Property set can either an object
    #  conforming to the IMutable property sheet interface or a dictionary (in
    #  which case the properties are not persistently mutable).
    #
    @security.private
    def getPropertiesForUser(self, user_or_group, request=None):
        """User -> IMutablePropertySheet || {}

        o User will implement IPropertiedUser. ???

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present
        """
        ugid = user_or_group.getId()
        try:
            if self.enumerateUsers(id=ugid) or self.enumerateGroups(id=ugid):
                return LDAPUserPropertySheet(user_or_group, self)
        except KeyError:
            pass
        return {}

    @security.private
    def setPropertiesForUser(self, user, propertysheet):
        """Set modified properties on the user persistently.

        Does nothing, it is called by MutablePropertySheet in
        setProperty and setProperties. This should not affect us at
        all as we handle setting of properties via our own
        LDAPPropertySheet
        """
        pass

    @security.private
    def deleteUser(self, user_id):
        """Remove properties stored for a user.

        Does nothing, if a user is deleted by ``doDeleteUser``, all it's
        properties are away as well.
        """
        pass

    # ##
    # plonepas_interfaces.plugins.IUserManagement
    # (including signature of pas_interfaces.IUserAdderPlugin)
    #
    @security.private
    def doAddUser(self, login, password):
        """ Add a user record to a User Manager, with the given login
            and password

        o Return a Boolean indicating whether a user was added or not
        """
        # XXX
        return False

    @security.private
    def doChangeUser(self, user_id, password, **kw):
        """Change a user's password (differs from role) roles are set in
        the pas engine api for the same but are set via a role
        manager)
        """
        if self.users:
            try:
                self.users.passwd(user_id, None, password)
            except KeyError:
                msg = '{0:s} is not an LDAP user.'.format(user_id)
                logger.warn(msg)
                raise RuntimeError(msg)

    @security.private
    def doDeleteUser(self, login):
        """Remove a user record from a User Manager, with the given login
        and password

        o Return a Boolean indicating whether a user was removed or
          not
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.capabilities.IDeleteCapability
    # (plone ui specific)
    #
    @security.public
    def allowDeletePrincipal(self, id):
        """True if this plugin can delete a certain user/group.
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.capabilities.IGroupCapability
    # (plone ui specific)
    #
    @security.public
    def allowGroupAdd(self, principal_id, group_id):
        """
        True if this plugin will allow adding a certain principal to
        a certain group.
        """
        # XXX
        return False

    @security.public
    def allowGroupRemove(self, principal_id, group_id):
        """
        True if this plugin will allow removing a certain principal
        from a certain group.
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.capabilities.IGroupIntrospection
    # (plone ui specific)

    # XXX: why dont we have security declarations here?

    def getGroupById(self, group_id):
        """
        Returns the portal_groupdata-ish object for a group
        corresponding to this id. None if group does not exist here!
        """
        group_id = decode_utf8(group_id)
        groups = self.groups
        if not groups or group_id not in groups.keys():
            return None
        ugmgroup = self.groups[group_id]
        title = ugmgroup.attrs.get('title', None)
        group = PloneGroup(ugmgroup.id, title).__of__(self)
        pas = self._getPAS()
        plugins = pas.plugins
        # add properties
        for propfinder_id, propfinder in \
                plugins.listPlugins(pas_interfaces.IPropertiesPlugin):

            data = propfinder.getPropertiesForUser(group, None)
            if not data:
                continue
            group.addPropertysheet(propfinder_id, data)
        # add subgroups
        group._addGroups(pas._getGroupsForPrincipal(group, None,
                                                    plugins=plugins))
        # add roles
        for rolemaker_id, rolemaker in \
                plugins.listPlugins(pas_interfaces.IRolesPlugin):

            roles = rolemaker.getRolesForPrincipal(group, None)
            if not roles:
                continue
            group._addRoles(roles)
        return group

    def getGroups(self):
        """
        Returns an iteration of the available groups
        """
        return map(self.getGroupById, self.getGroupIds())

    def getGroupIds(self):
        """
        Returns a list of the available groups (ids)
        """
        return self.groups and self.groups.ids or []

    def getGroupMembers(self, group_id):
        """
        return the members of the given group
        """
        try:
            group = self.groups[group_id]
        except (KeyError, TypeError):
            return ()
        return tuple(group.member_ids)

    # ##
    # plonepas_interfaces.capabilities.IPasswordSetCapability
    # (plone ui specific)
    #
    @security.public
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
