# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from BTrees import OOBTree
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPProps
from node.ext.ldap.interfaces import ILDAPUsersConfig
from node.ext.ldap.ugm import Ugm
from pas.plugins.ldap.cache import get_plugin_cache
from pas.plugins.ldap.interfaces import ILDAPPlugin
from pas.plugins.ldap.interfaces import VALUE_NOT_CACHED
from pas.plugins.ldap.sheet import LDAPUserPropertySheet
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PlonePAS import interfaces as plonepas_interfaces
from Products.PlonePAS.plugins.group import PloneGroup
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PluggableAuthService.permissions import ManageGroups
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from six.moves import map
from zope.interface import implementer

import ldap
import logging
import os
import six
import time


logger = logging.getLogger("pas.plugins.ldap")
zmidir = os.path.join(os.path.dirname(__file__), "zmi")

if six.PY2:
    process_time = time.clock
else:
    process_time = time.process_time

LDAP_ERROR_LOG_TIMEOUT = float(
    os.environ.get("PAS_PLUGINS_LDAP_ERROR_LOG_TIMEOUT", 300.0)
)
LDAP_LONG_RUNNING_LOG_THRESHOLD = float(
    os.environ.get("PAS_PLUGINS_LDAP_LONG_RUNNING_LOG_THRESHOLD", 5.0)
)


def manage_addLDAPPlugin(dispatcher, id, title="", RESPONSE=None, **kw):
    """Create an instance of a LDAP Plugin.
    """
    ldapplugin = LDAPPlugin(id, title, **kw)
    dispatcher._setObject(ldapplugin.getId(), ldapplugin)
    if RESPONSE is not None:
        RESPONSE.redirect("manage_workspace")


manage_addLDAPPluginForm = PageTemplateFile(
    os.path.join(zmidir, "add_plugin.pt"), globals(), __name__="addLDAPPlugin"
)


def ldap_error_handler(prefix, default=None):
    """decorator, deals with non-working LDAP"""

    def _decorator(original_method, *args, **kwargs):
        def _wrapper(self, *args, **kwargs):
            # look if error is in timeout phase
            if hasattr(self, "_v_ldaperror_timeout"):
                waiting = time.time() - self._v_ldaperror_timeout
                if waiting < LDAP_ERROR_LOG_TIMEOUT:
                    logger.debug(
                        "{0}: retry wait {1:0.5f} of {2:0.0f}s -> {3}".format(
                            prefix, waiting, LDAP_ERROR_LOG_TIMEOUT,
                            self._v_ldaperror_msg,
                        )
                    )
                    return default
            try:
                # call original method - get metrics
                start = process_time()
                result = original_method(self, *args, **kwargs)
                delta_t = process_time() - start
                msg = "Call of {0!r} took {1:0.4f}s".format(original_method, delta_t)
                if delta_t < LDAP_LONG_RUNNING_LOG_THRESHOLD:
                    logger.debug(msg)
                else:
                    logger.error(msg)
                return result

            # handle errors
            except ldap.LDAPError as e:
                self._v_ldaperror_msg = str(e)
                self._v_ldaperror_timeout = time.time()
                logger.exception("LDAPError in {0}".format(prefix))
                return default
            except Exception as e:
                self._v_ldaperror_msg = str(e)
                self._v_ldaperror_timeout = time.time()
                logger.exception("Error in {0}".format(prefix))
                return default

        return _wrapper

    return _decorator


@implementer(
    ILDAPPlugin,
    pas_interfaces.IAuthenticationPlugin,
    pas_interfaces.IGroupEnumerationPlugin,
    pas_interfaces.IGroupsPlugin,
    pas_interfaces.IPropertiesPlugin,
    pas_interfaces.IUserEnumerationPlugin,
    pas_interfaces.IRolesPlugin,
    plonepas_interfaces.capabilities.IDeleteCapability,
    plonepas_interfaces.capabilities.IGroupCapability,
    plonepas_interfaces.capabilities.IPasswordSetCapability,
    plonepas_interfaces.group.IGroupManagement,
    plonepas_interfaces.group.IGroupIntrospection,
    plonepas_interfaces.plugins.IMutablePropertiesPlugin,
    plonepas_interfaces.plugins.IUserManagement,
)
class LDAPPlugin(BasePlugin):
    """Glue layer for making node.ext.ldap available to PAS.
    """

    security = ClassSecurityInfo()
    meta_type = "LDAP Plugin"
    manage_options = (
        {"label": "LDAP Settings", "action": "manage_ldapplugin"},
    ) + BasePlugin.manage_options

    # Tell PAS not to swallow our exceptions
    _dont_swallow_my_exceptions = False

    def __init__(self, id, title=None, **kw):
        self._setId(id)
        self.title = title
        self.init_settings()
        self.plugin_caching = True

    def init_settings(self):
        self.settings = OOBTree.OOBTree()

    @security.private
    def is_plugin_active(self, iface):
        pas = self._getPAS()
        ids = pas.plugins.listPluginIds(iface)
        return self.getId() in ids

    @property
    @security.private
    def groups_enabled(self):
        return self.groups is not None

    @property
    @security.private
    def users_enabled(self):
        return self.users is not None

    @property
    def _ldap_props(self):
        return ILDAPProps(self)

    def _ugm(self):
        plugin_cache = get_plugin_cache(self)
        ugm = plugin_cache.get()
        if ugm is not VALUE_NOT_CACHED:
            return ugm
        ucfg = ILDAPUsersConfig(self)
        gcfg = ILDAPGroupsConfig(self)
        ugm = Ugm(props=self._ldap_props, ucfg=ucfg, gcfg=gcfg, rcfg=None)
        plugin_cache.set(ugm)
        return ugm

    @property
    @ldap_error_handler("groups")
    @security.private
    def groups(self):
        return self._ugm().groups

    @property
    @ldap_error_handler("users")
    @security.private
    def users(self):
        return self._ugm().users

    @property
    @security.protected(ManageUsers)
    def ldaperror(self):
        if hasattr(self, "_v_ldaperror_msg"):
            waiting = time.time() - self._v_ldaperror_timeout
            if waiting < LDAP_ERROR_LOG_TIMEOUT:
                return self._v_ldaperror_msg + " (for %0.2fs)" % waiting
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
    @ldap_error_handler("authenticateCredentials")
    @security.public
    def authenticateCredentials(self, credentials):
        """credentials -> (userid, login)

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """
        default = None
        if not self.is_plugin_active(pas_interfaces.IAuthenticationPlugin):
            return default
        login = credentials.get("login")
        pw = credentials.get("password")
        if not (login and pw):
            return default
        logger.debug("credentials: %s" % credentials)
        users = self.users
        if not users:
            return default
        userid = users.authenticate(login, pw)
        if userid:
            logger.info("logged in %s" % userid)
            return (userid, login)
        return default

    # ##
    # pas_interfaces.IGroupEnumerationPlugin
    #
    #  Allow querying groups by ID, and searching for groups.
    #
    @security.private
    def enumerateGroups(
        self, id=None, exact_match=False, sort_by=None, max_results=None, **kw
    ):
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
        default = ()
        if not self.is_plugin_active(pas_interfaces.IGroupEnumerationPlugin):
            return default
        groups = self.groups
        if not groups:
            return default
        if id:
            kw["id"] = id
        if not kw:  # show all
            matches = groups.ids
        else:
            try:
                matches = groups.search(criteria=kw, exact_match=exact_match)
            # raised if exact_match and result not unique.
            except ValueError:
                return default
        if sort_by == "id":
            matches = sorted(matches)
        pluginid = self.getId()
        ret = [dict(id=_id, pluginid=pluginid) for _id in matches]
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
        default = tuple()
        if not self.is_plugin_active(pas_interfaces.IGroupsPlugin):
            return default
        users = self.users
        if not users:
            return default
        try:
            ugm_principal = self.users[principal.getId()]
        except KeyError:
            # XXX: that's where group in group will happen, but so far
            # group nodes do not provide membership info so we just
            # return if there is no user
            return default
        try:
            return ugm_principal.group_ids
        except Exception:
            logger.exception("Problems getting group_ids!")
        return default

    # ##
    # pas_interfaces.IUserEnumerationPlugin
    #
    #   Allow querying users by ID, and searching for users.
    #
    @ldap_error_handler("enumerateUsers", default=tuple())
    @security.private
    def enumerateUsers(
        self,
        id=None,
        login=None,
        exact_match=False,
        sort_by=None,
        max_results=None,
        **kw
    ):
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
        default = tuple()
        if not self.is_plugin_active(pas_interfaces.IUserEnumerationPlugin):
            return default
        # XXX: sort_by in node.ext.ldap
        if login:
            if not isinstance(login, six.string_types):
                # XXX
                raise NotImplementedError("sequence is not supported yet.")
            kw["login"] = login
        # pas search users gives both login and name if login is meant
        if "login" in kw and "name" in kw:
            del kw["name"]
        if id:
            if not isinstance(id, six.string_types):
                # XXX
                raise NotImplementedError("sequence is not supported yet.")
            kw["id"] = id
        users = self.users
        if not users:
            return default
        if not exact_match:
            for key in kw:
                value = kw[key]
                if not value.endswith("*"):
                    kw[key] = value + "*"
        try:
            matches = users.search(
                criteria=kw, attrlist=("login",), exact_match=exact_match
            )
        # raised if exact_match and result not unique.
        except ValueError:
            return default
        pluginid = self.getId()
        ret = list()
        for id_, attrs in matches:
            ret.append({"id": id_, "login": attrs["login"][0], "pluginid": pluginid})
        if max_results and len(ret) > max_results:
            ret = ret[:max_results]
        return ret

    # ##
    # pas_interfaces.plugins.IRolesPlugin
    #
    def getRolesForPrincipal(self, principal, request=None):
        default = ()
        users = self.users
        if not users:
            return default
        if self.enumerateUsers(id=principal.getId()):
            return ('Member', )
        return default

    @security.private
    def updateUser(self, user_id, login_name):
        """ Update the login name of the user with id user_id.

        The plugin must return True (or any truth value) to indicate a
        successful update, also when no update was needed.

        When updating a login name makes no sense for a plugin (most
        likely because it does not actually store login names) and it
        does not do anything, it must return None or False.
        """
        # XXX
        # if not self.is_plugin_active(pas_interfaces.IUserEnumerationPlugin):
        #    return default
        return False

    @security.private
    def updateEveryLoginName(self, quit_on_first_error=True):
        """Update login names of all users to their canonical value.

        This should be done after changing the login_transform
        property of PAS.

        You can set quit_on_first_error to False to report all errors
        before quitting with an error.  This can be useful if you want
        to know how many problems there are, if any.
        """
        # XXX
        # if not self.is_plugin_active(pas_interfaces.IUserEnumerationPlugin):
        #    return default
        return

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
        default = {}
        if not self.is_plugin_active(pas_interfaces.IPropertiesPlugin):
            return default
        ugid = user_or_group.getId()
        if not isinstance(ugid, six.text_type):
            ugid = ugid.decode("utf-8")
        try:
            if self.enumerateUsers(id=ugid) or self.enumerateGroups(id=ugid):
                return LDAPUserPropertySheet(user_or_group, self)
        except KeyError:
            pass
        return default

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
                msg = "{0:s} is not an LDAP user.".format(user_id)
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

    @security.public
    def getGroupById(self, group_id):
        """
        Returns the portal_groupdata-ish object for a group
        corresponding to this id. None if group does not exist here!
        """
        default = None
        if not self.is_plugin_active(plonepas_interfaces.group.IGroupIntrospection):
            return default
        if group_id is None:
            return None
        if not isinstance(group_id, six.text_type):
            group_id = group_id.decode("utf8")
        groups = self.groups
        if not groups or group_id not in list(groups.keys()):
            return default
        ugmgroup = self.groups[group_id]
        title = ugmgroup.attrs.get("title", None)
        group = PloneGroup(ugmgroup.id, title).__of__(self)
        pas = self._getPAS()
        plugins = pas.plugins
        # add properties
        for propfinder_id, propfinder in plugins.listPlugins(
            pas_interfaces.IPropertiesPlugin
        ):

            data = propfinder.getPropertiesForUser(group, None)
            if not data:
                continue
            group.addPropertysheet(propfinder_id, data)
        # add subgroups
        group._addGroups(pas._getGroupsForPrincipal(group, None, plugins=plugins))
        # add roles
        for rolemaker_id, rolemaker in plugins.listPlugins(pas_interfaces.IRolesPlugin):

            roles = rolemaker.getRolesForPrincipal(group, None)
            if not roles:
                continue
            group._addRoles(roles)
        return group

    @security.private
    def getGroups(self):
        """
        Returns an iteration of the available groups
        """
        # Checking self.is_plugin_active(
        # plonepas_interfaces.group.IGroupIntrospection)
        # is done in self.getGroupIds() already.
        return list(map(self.getGroupById, self.getGroupIds()))

    @security.private
    def getGroupIds(self):
        """
        Returns a list of the available groups (ids)
        """
        default = []
        if not self.is_plugin_active(plonepas_interfaces.group.IGroupIntrospection):
            return default
        return self.groups and self.groups.ids or default

    @security.private
    def getGroupMembers(self, group_id):
        """
        return the members of the given group
        """
        default = ()
        if not self.is_plugin_active(plonepas_interfaces.group.IGroupIntrospection):
            return default
        try:
            group = self.groups[group_id]
        except (KeyError, TypeError):
            return default
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
            res = self.users.search(criteria={"id": id}, attrlist=(), exact_match=True)
            return len(res) > 0
        except ValueError:
            return False


InitializeClass(LDAPPlugin)
