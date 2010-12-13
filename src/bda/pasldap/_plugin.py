import ldap
import logging
logger = logging.getLogger('bda.pasldap')

from zope.interface import implements
from zope.component import getUtility
from bda.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig)
from bda.ldap.users import LDAPUsers
#from bda.ldap.groups import LDAPGroups
from Products.CMFCore.interfaces import ISiteRoot
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PlonePAS import interfaces as plonepas_interfaces
from bda.pasldap.sheet import LDAPUserPropertySheet
from bda.pasldap.utils import (
    debug,
    ifnotenabledreturn)


class LDAPPlugin(BasePlugin, object):
    """Glue layer for making bda.ldap available to PAS.
    """
    implements(
        pas_interfaces.IAuthenticationPlugin,
        pas_interfaces.IUserEnumerationPlugin,
        pas_interfaces.IPropertiesPlugin,
        plonepas_interfaces.plugins.IMutablePropertiesPlugin,
        plonepas_interfaces.plugins.IUserManagement,
        plonepas_interfaces.capabilities.IDeleteCapability,
        plonepas_interfaces.capabilities.IPasswordSetCapability)
    
    _dont_swallow_my_exceptions = True # Tell PAS not to swallow our exceptions
    meta_type = 'BDALDAPPlugin'
    
    def __init__(self, id, title=None):
        self.id = id
        self.title = title
    
    def reset(self):
        delattr(self, '_v_users')
    
    @property
    def enabled(self):
        return self.users is not None

    @property
    def users(self):
        try:
            return self._v_users
        except AttributeError:
            self._init_users()
            if hasattr(self, '_v_users'):
                return self._v_users
            return None

    def _init_users(self):
        site = getUtility(ISiteRoot)
        props = ILDAPProps(site)
        ucfg = ILDAPUsersConfig(site)
        #gcfg = ILDAPGroupsConfig(site)
        try:
            self._v_users = LDAPUsers(props, ucfg)
#        except ValueError, e:
#            pass
        except Exception, e:
            logger.error('caught: %s.' % str(e))
        #self._v_groups = LDAPGroups(props, gcfg)
    
    ###
    # pas_interfaces.IAuthenticationPlugin
    #
    #  Map credentials to a user ID.
    #
    @ifnotenabledreturn(None)
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
        uid = self.users.authenticate(login=login, pw=pw)
        if uid:
            return (uid, login)
    
    ###
    # pas_interfaces.IUserEnumerationPlugin
    #
    #   Allow querying users by ID, and searching for users.
    #    o XXX:  can these be done by a single plugin?
    #
    @ifnotenabledreturn(tuple())
    @debug(['userenumeration'])
    def enumerateUsers(self, id=None, login=None, exact_match=False,
            sort_by=None, max_results=None, **kws):
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
        # TODO: max_results in bda.ldap
        # TODO: sort_by in bda.ldap
        if id:
            kws['id'] = id
        if login:
            kws['login'] = login
        matches = self.users.search(
            criteria=kws,
            attrlist=('login',),
            exact_match=exact_match
        )
        pluginid = self.getId()
        ret = [dict(
            id=id.encode('ascii', 'replace'),
            login=attrs['login'][0], #XXX: see bda.ldap.users.Users.search
            pluginid=pluginid,
            ) for id, attrs in matches]
        return ret
    
    ###
    # plonepas_interfaces.plugins.IMutablePropertiesPlugin
    # (including signature of pas_interfaces.IPropertiesPlugin)
    #
    #  Return a property set for a user. Property set can either an object
    #  conforming to the IMutable property sheet interface or a dictionary (in
    #  which case the properties are not persistently mutable).
    #

    @ifnotenabledreturn(dict())
    def getPropertiesForUser(self, user, request=None):
        """User -> IMutablePropertySheet || {}

        o User will implement IPropertiedUser. ???

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present
        """
        return LDAPUserPropertySheet(user, self)
    
    @ifnotenabledreturn(None)
    def setPropertiesForUser(self, user, propertysheet):
        """Set modified properties on the user persistently.

        Does nothing, it is called by MutablePropertySheet in setProperty and
        setProperties. This should not affect us at all
        """
        pass
    
    @ifnotenabledreturn(None)
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

    @ifnotenabledreturn(False)
    def doChangeUser(self, login, password, **kw):
        """Change a user's password (differs from role) roles are set in
        the pas engine api for the same but are set via a role
        manager)
        """
        self.users.passwd(login, None, password)

    @ifnotenabledreturn(False)
    def doDeleteUser(self, login):
        """Remove a user record from a User Manager, with the given login
        and password

        o Return a Boolean indicating whether a user was removed or
          not
        """
        # XXX
        return False
    
    ###
    # plonepas_interfaces.capabilities.IPasswordSetCapability
    # (plone ui specific)
    #
    @ifnotenabledreturn(False)
    def allowPasswordSet(self, id):
        """True if this plugin can set the password of a certain user.
        """
        # XXX: should just be bool(self.get('id')), currently not because user
        # might be deleted and we don't know about
        return len(self.users.search(criteria={'id': id},
                                     attrlist=(),
                                     exact_match=True)) > 0
    
    ###
    # plonepas_interfaces.capabilities.IDeleteCapability
    # (plone ui specific)
    #
    @ifnotenabledreturn(False)
    def allowDeletePrincipal(self, id):
        """True if this plugin can delete a certain user/group.
        """
        # XXX
        return False
