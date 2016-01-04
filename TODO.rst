
TODO
====

See also
'Issue-Tracker <https://github.com/collective/pas.plugins.ldap/issues>`_

Milestone 2.0
-------------

- remove portrait monkey patch
- add/delete users
- add/delete groups
- add flags for readonly groups and users
- modes for only groups or only users from ldap
- SSL/TLS configuration TTW
- creation defaults TTW
- group in group (depends on: node.ext.ldap: group.groups support)
- roles from ldap
- Option on LDAP inspector whether to use query filters from users and groups
  config

Related TODO
------------

- Fix ``yafowil.plone`` resource registration for Plone 5

Misc
----

::

    node.ext.ldap/src/node/ext/ldap/session.py:51:
    UnicodeWarning: Unicode equal comparison failed to convert both arguments to
    Unicode - interpreting them as being unequal
        if queryFilter in ('', u'', None):
