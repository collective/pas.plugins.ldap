
TODO
====

see also 'Issue-Tracker <https://github.com/collective/pas.plugins.ldap/issues>`_

Milestone 1.1
-------------

- remove portrait monkey patch 
- add/delete users
- add/delete groups
- add flags for readonly groups and users
- modes for only groups or only users from ldap

Nice-to-Have
------------

- group in group (depends on: node.ext.ldap: group.groups support)
- roles from ldap

Misc
----
::

    node.ext.ldap/src/node/ext/ldap/session.py:51: 
    UnicodeWarning: Unicode equal comparison failed to convert both arguments to 
    Unicode - interpreting them as being unequal
        if queryFilter in ('', u'', None):


