==================
Test of the plugin
==================

Setup
=====

Basics
------

.. code-block:: pycon

    >>> app = layer['app']
    >>> pas = app.acl_users
    >>> pas
    <PluggableAuthService at /acl_users>


Create
------

.. code-block:: pycon

    >>> from pas.plugins.ldap.setuphandlers import _addPlugin
    >>> _addPlugin(app.acl_users)
    >>> sorted(pas.objectIds())
    ['chooser', 'credentials_basic_auth', 'credentials_cookie_auth', 'pasldap',
    'plugins', 'roles', 'sniffer', 'users']

    >>> ldap = pas['pasldap']
    >>> ldap
    <LDAPPlugin at /acl_users/pasldap>

turn off plugin_caching for testing, because test request has strange
behaviour:

.. code-block:: pycon

    >>> ldap.plugin_caching = False


PAS Plugins
===========

IAuthenticationPlugin
---------------------

.. code-block:: pycon

    >>> ldap.authenticateCredentials({'login':'cn0', 'password': 'secret0'})
    ('uid0', 'cn0')

    >>> ldap.authenticateCredentials({'login':'admin', 'password': 'admin'})

    >>> ldap.authenticateCredentials({'login':'nonexist', 'password': 'dummy'})


IGroupEnumerationPlugin
-----------------------

Signature is ``enumerateGroups(self, id=None, exact_match=False, sort_by=None,
max_results=None, **kw)``

.. code-block:: pycon

    >>> [sorted(group.items()) for group in ldap.enumerateGroups(id='group2')]
    [[('id', 'group2'), ('pluginid', 'pasldap')]]

    >>> print(sorted([_['id'] for _ in ldap.enumerateGroups(id='group*')]))
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6',
    'group7', 'group8', 'group9']

    >>> [_['id'] for _ in ldap.enumerateGroups(id='group*', sort_by='id')]
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6',
    'group7', 'group8', 'group9']

    >>> ldap.enumerateGroups(id='group*', exact_match=True)
    ()

    >>> [sorted(group.items()) for group in ldap.enumerateGroups(id='group5', exact_match=True)]
    [[('id', 'group5'), ('pluginid', 'pasldap')]]

    >>> len(ldap.enumerateGroups(id='group*', max_results=3))
    3


IGroupsPlugin
-------------

.. code-block:: pycon

    >>> user = pas.getUserById('uid9')
    >>> ldap.getGroupsForPrincipal(user)
    ['group9']

    >>> user = pas.getUserById('uid1')
    >>> ldap.getGroupsForPrincipal(user)
    ['group1', 'group2', 'group3', 'group4', 'group5',
    'group6', 'group7', 'group8', 'group9']

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

.. code-block:: pycon

    >>> [sorted(user.items()) for user in ldap.enumerateUsers(id='uid1')]
    [[('id', 'uid1'), ('login', 'cn1'), ('pluginid', 'pasldap')]]

    >>> [sorted(user.items()) for user in ldap.enumerateUsers(id='uid*')]
    [[('id', 'uid0'), ('login', 'cn0'), ('pluginid', 'pasldap')],
    [('id', 'uid1'), ('login', 'cn1'), ('pluginid', 'pasldap')],
    [('id', 'uid2'), ('login', 'cn2'), ('pluginid', 'pasldap')],
    [('id', 'uid3'), ('login', 'cn3'), ('pluginid', 'pasldap')],
    [('id', 'uid4'), ('login', 'cn4'), ('pluginid', 'pasldap')],
    [('id', 'uid5'), ('login', 'cn5'), ('pluginid', 'pasldap')],
    [('id', 'uid6'), ('login', 'cn6'), ('pluginid', 'pasldap')],
    [('id', 'uid7'), ('login', 'cn7'), ('pluginid', 'pasldap')],
    [('id', 'uid8'), ('login', 'cn8'), ('pluginid', 'pasldap')],
    [('id', 'uid9'), ('login', 'cn9'), ('pluginid', 'pasldap')]]

    >>> [_['id'] for _ in ldap.enumerateUsers(id='uid*', sort_by='id')]
    ['uid0', 'uid1', 'uid2', 'uid3', 'uid4', 'uid5', 'uid6', 'uid7', 'uid8',
    'uid9']

    >>> ldap.enumerateUsers(id='uid*', exact_match=True)
    ()

    >>> [sorted(user.items()) for user in ldap.enumerateUsers(id='uid4', exact_match=True)]
    [[('id', 'uid4'), ('login', 'cn4'), ('pluginid', 'pasldap')]]

    >>> len(ldap.enumerateUsers(id='uid*', max_results=3))
    3

    >>> [sorted(user.items()) for user in ldap.enumerateUsers(login='cn1')]
    [[('id', 'uid1'), ('login', 'cn1'), ('pluginid', 'pasldap')]]


IDeleteCapability
-----------------

It's not allowed to delete a principal using this plugin. We may change this
later and make it configurable:

.. code-block:: pycon

    >>> ldap.allowDeletePrincipal('uid0')
    False

    >>> ldap.allowDeletePrincipal('unknownuser')
    False


Picklable
---------

In order to cache propertysheets it must be picklable:

.. code-block:: pycon

    >>> from Acquisition import aq_base
    >>> import pickle
    >>> len(pickle.dumps(aq_base(ldap))) > 200
    True


PlonePAS
========

IGroupCapability
----------------

By now adding groups is not allowed.  We may change this later and make it
configurable:

.. code-block:: pycon

    >>> ldap.allowGroupAdd('uid0', 'group0')
    False

Same for deletion of groups:

.. code-block:: pycon

    >>> ldap.allowGroupRemove('uid0', 'group0')
    False


IGroupIntrospection
-------------------

getGroupById returns the portal_groupdata-ish object for a group corresponding
to this id:

.. code-block:: pycon

    >>> ldap.getGroupById('group0')
    <PloneGroup 'group0'>

    >>> print(ldap.getGroupById('non-existent'))
    None

list all groups ids:

.. code-block:: pycon

    >>> ldap.getGroupIds()
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5',
    'group6', 'group7', 'group8', 'group9']

list all groups:

.. code-block:: pycon

    >>> ldap.getGroups()
    [<PloneGroup 'group0'>, <PloneGroup 'group1'>, <PloneGroup 'group2'>,
    <PloneGroup 'group3'>, <PloneGroup 'group4'>, <PloneGroup 'group5'>,
    <PloneGroup 'group6'>, <PloneGroup 'group7'>, <PloneGroup 'group8'>,
    <PloneGroup 'group9'>]

list all members of a group:

.. code-block:: pycon

    >>> ldap.getGroupMembers('group3')
    ('uid1', 'uid2', 'uid3')


IPasswordSetCapability
----------------------

User are able to set the password:

.. code-block:: pycon

    >>> ldap.allowPasswordSet('uid0')
    True

Not so for groups:

.. code-block:: pycon

    >>> ldap.allowPasswordSet('group0')
    False

Also not for non existent:

.. code-block:: pycon

    >>> ldap.allowPasswordSet('ghost')
    False


IGroupManagement
----------------

See also ``IGroupCapability`` - for now we dont support this:

.. code-block:: pycon

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

Get works:

.. code-block:: pycon

    >>> user = pas.getUserById('uid0')
    >>> sheet = ldap.getPropertiesForUser(user, request=None)
    >>> sheet
    <pas.plugins.ldap.sheet.LDAPUserPropertySheet ... at ...>

    >>> sheet.getProperty('mail')
    'uid0@groupOfNames_10_10.com'

Set does nothing, but the sheet itselfs set immediatly:

.. code-block:: pycon

    >>> from pas.plugins.ldap.sheet import LDAPUserPropertySheet
    >>> sheet = LDAPUserPropertySheet(user, ldap)
    >>> sheet.getProperty('mail')
    'uid0@groupOfNames_10_10.com'

    >>> sheet.setProperty(None, 'mail', 'foobar@example.com')
    >>> sheet.getProperty('mail')
    'foobar@example.com'

    >>> sheet2 = LDAPUserPropertySheet(user, ldap)
    >>> sheet2.getProperty('mail')
    'foobar@example.com'

    >>> ldap.deleteUser('cn9')

In order to cache propertysheets it must be picklable:

.. code-block:: pycon

    >>> len(pickle.dumps(sheet2)) > 600
    True


IUserManagement
---------------

Password change and attributes at once with ``doChangeUser``:

.. code-block:: pycon

    >>> ldap.doChangeUser('uid9', 'geheim') is None
    True

    >>> ldap.authenticateCredentials({'login':'cn9', 'password': 'geheim'})
    ('uid9', 'cn9')


We dont support user deletion for now. We may change this later and make it
configurable:

.. code-block:: pycon

    >>> ldap.doDeleteUser('uid0')
    False
