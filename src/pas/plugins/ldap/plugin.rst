==================
Test of the plugin
==================

Setup
=====

Basics
------

::
    >>> app = layer['app']
    >>> pas = app.acl_users
    >>> pas
    <PluggableAuthService at /acl_users>

Create
------

::
    >>> from pas.plugins.ldap.setuphandlers import _addPlugin
    >>> _addPlugin(app.acl_users)
    >>> sorted(pas.objectIds())
    ['chooser', 'credentials_basic_auth', 'credentials_cookie_auth', 'pasldap',
    'plugins', 'roles', 'sniffer', 'users']

    >>> ldap = pas['pasldap']
    >>> ldap
    <LDAPPlugin at /acl_users/pasldap>

turn off plugin_caching for testing, because test request has strange
behaviour::

    >>> ldap.plugin_caching = False

PAS Plugins
===========

IAuthenticationPlugin
---------------------

::

    >>> ldap.authenticateCredentials({'login':'cn0', 'password': 'secret0'})
    (u'uid0', 'cn0')

    >>> ldap.authenticateCredentials({'login':'admin', 'password': 'admin'})

    >>> ldap.authenticateCredentials({'login':'nonexist', 'password': 'dummy'})


IGroupEnumerationPlugin
-----------------------

Signature is ``enumerateGroups(self, id=None, exact_match=False, sort_by=None,
max_results=None, **kw)``

::

    >>> ldap.enumerateGroups(id='group2')
    [{'pluginid': 'pasldap', 'id': 'group2'}]

    >>> print sorted([_['id'] for _ in ldap.enumerateGroups(id='group*')])
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6',
    'group7', 'group8', 'group9']

    >>> [_['id'] for _ in ldap.enumerateGroups(id='group*', sort_by='id')]
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6',
    'group7', 'group8', 'group9']

    >>> ldap.enumerateGroups(id='group*', exact_match=True)
    ()

    >>> ldap.enumerateGroups(id='group5', exact_match=True)
    [{'pluginid': 'pasldap', 'id': 'group5'}]

    >>> len(ldap.enumerateGroups(id='group*', max_results=3))
    3


IGroupsPlugin
-------------

::

    >>> user = pas.getUserById('uid9')
    >>> ldap.getGroupsForPrincipal(user)
    [u'group9']

    >>> user = pas.getUserById('uid1')
    >>> ldap.getGroupsForPrincipal(user)
    [u'group1', u'group2', u'group3', u'group4', u'group5',
    u'group6', u'group7', u'group8', u'group9']

    >>> user = pas.getUserById('uid0')
    >>> ldap.getGroupsForPrincipal(user)
    []

IPropertiesPlugin
-----------------

see PlonePAS, IMutablePropertiesPlugin

IUserEnumerationPlugin
----------------------

Signature is ``enumerateUsers( id=None, login=None, exact_match=False,
sort_by=None, max_results=None, **kw)``

::

    >>> ldap.enumerateUsers(id='uid1')
    [{'login': u'cn1', 'pluginid': 'pasldap', 'id': 'uid1'}]

    >>> ldap.enumerateUsers(id='uid*')
    [{'login': u'cn0', 'pluginid': 'pasldap', 'id': 'uid0'},
    {'login': u'cn1', 'pluginid': 'pasldap', 'id': 'uid1'},
    {'login': u'cn2', 'pluginid': 'pasldap', 'id': 'uid2'},
    {'login': u'cn3', 'pluginid': 'pasldap', 'id': 'uid3'},
    {'login': u'cn4', 'pluginid': 'pasldap', 'id': 'uid4'},
    {'login': u'cn5', 'pluginid': 'pasldap', 'id': 'uid5'},
    {'login': u'cn6', 'pluginid': 'pasldap', 'id': 'uid6'},
    {'login': u'cn7', 'pluginid': 'pasldap', 'id': 'uid7'},
    {'login': u'cn8', 'pluginid': 'pasldap', 'id': 'uid8'},
    {'login': u'cn9', 'pluginid': 'pasldap', 'id': 'uid9'}]

    >>> [_['id'] for _ in ldap.enumerateUsers(id='uid*', sort_by='id')]
    ['uid0', 'uid1', 'uid2', 'uid3', 'uid4', 'uid5', 'uid6', 'uid7', 'uid8',
    'uid9']

    >>> ldap.enumerateUsers(id='uid*', exact_match=True)
    ()

    >>> ldap.enumerateUsers(id='uid4', exact_match=True)
    [{'login': u'cn4', 'pluginid': 'pasldap', 'id': 'uid4'}]

    >>> len(ldap.enumerateUsers(id='uid*', max_results=3))
    3

    >>> ldap.enumerateUsers(login='cn1')
    [{'login': u'cn1', 'pluginid': 'pasldap', 'id': 'uid1'}]


IDeleteCapability
-----------------

It's not allowed to delete a principal using this plugin. We may change this
later and make it configurable::

    >>> ldap.allowDeletePrincipal('uid0')
    False

    >>> ldap.allowDeletePrincipal('unknownuser')
    False


Picklable
---------

In order to cache propertysheets it must be picklable::

    >>> from Acquisition import aq_base
    >>> import pickle
    >>> len(pickle.dumps(aq_base(ldap))) > 200
    True


PlonePAS
========

IGroupCapability
----------------

By now adding groups is not allowed.  We may change this later and make it
configurable::

    >>> ldap.allowGroupAdd('uid0', 'group0')
    False

Same for deletion of groups::

    >>> ldap.allowGroupRemove('uid0', 'group0')
    False

IGroupIntrospection
-------------------

getGroupById returns the portal_groupdata-ish object for a group corresponding
to this id::

    >>> ldap.getGroupById('group0')
    <PloneGroup u'group0'>

    >>> print ldap.getGroupById('non-existent')
    None

list all groups ids::

    >>> ldap.getGroupIds()
    [u'group0', u'group1', u'group2', u'group3', u'group4', u'group5',
    u'group6', u'group7', u'group8', u'group9']

list all groups::

    >>> ldap.getGroups()
    [<PloneGroup u'group0'>, <PloneGroup u'group1'>, <PloneGroup u'group2'>,
    <PloneGroup u'group3'>, <PloneGroup u'group4'>, <PloneGroup u'group5'>,
    <PloneGroup u'group6'>, <PloneGroup u'group7'>, <PloneGroup u'group8'>,
    <PloneGroup u'group9'>]

list all members of a group::

    >>> ldap.getGroupMembers('group3')
    (u'uid1', u'uid2', u'uid3')

IPasswordSetCapability
----------------------

User are able to set the password::

    >>> ldap.allowPasswordSet('uid0')
    True

Not so for groups::

    >>> ldap.allowPasswordSet('group0')
    False

Also not for non existent::

    >>> ldap.allowPasswordSet('ghost')
    False

IGroupManagement
----------------

See also ``IGroupCapability`` - for now we dont support this::

    >>> ldap.addGroup(id)
    False

    >>> ldap.addPrincipalToGroup('uid0', 'group0')
    False

    >>> ldap.updateGroup('group9', **{})
    False

    >>> ldap.setRolesForGroup('uid0', roles=('Manager'))
    False

    >>> ldap.removeGroup('group0')
    False

    >>> ldap.removePrincipalFromGroup('uid1', 'group1')
    False

IMutablePropertiesPlugin
------------------------

Get works::

    >>> user = pas.getUserById('uid0')
    >>> sheet = ldap.getPropertiesForUser(user, request=None)
    >>> sheet
    <pas.plugins.ldap.sheet.LDAPUserPropertySheet instance at ...>

    >>> sheet.getProperty('mail')
    u'uid0@groupOfNames_10_10.com'

Set does nothing, but the sheet itselfs set immediatly::

    >>> from pas.plugins.ldap.sheet import LDAPUserPropertySheet
    >>> sheet = LDAPUserPropertySheet(user, ldap)
    >>> sheet.getProperty('mail')
    u'uid0@groupOfNames_10_10.com'

    >>> sheet.setProperty(None, 'mail', u'foobar@example.com')
    >>> sheet.getProperty('mail')
    u'foobar@example.com'

    >>> sheet2 = LDAPUserPropertySheet(user, ldap)
    >>> sheet2.getProperty('mail')
    u'foobar@example.com'

    >>> ldap.deleteUser('cn9')


In order to cache propertysheets it must be picklable::

    >>> len(pickle.dumps(sheet2)) > 600
    True


IUserManagement
---------------

Password change and attributes at once with ``doChangeUser``::

    >>> ldap.doChangeUser('uid9', 'geheim') is None
    True

    >>> ldap.authenticateCredentials({'login':'cn9', 'password': 'geheim'})
    (u'uid9', 'cn9')


We dont support user deletion for now. We may change this later and make it
configurable::

    >>> ldap.doDeleteUser('uid0')
    False
