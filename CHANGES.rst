
History
=======

1.5 (2016-10-06)
----------------

- No changes.


1.5b1 (2016-09-09)
------------------

- GroupEnumeration paged.
  [jensens]

- UserEnumeration paged.
  [jensens]

- Add page_size server property.
  [jensens]

- Fix LDAP check.
  [jensens]

- Split profiles for Plone 4 and 5.
  [jensens]

- fix tests for Plone 5
  [jensens]

- Fixed LDAP errors not handled. This prevent leave the site broken
  just after the installation of the plugin
  [keul]

- Adopt LDAP instector to use DN instead of RDN for node identification.
  [rnix]

- Add dummy ``defaults`` setting to ``UsersConfig`` and ``GroupsConfig``
  adapters. These defaults are used to set child creation defaults, thus
  concrete implementation is postponed until user and group creation is
  supported through plone UI.
  [rnix]

- Add ``ignore_cert`` setting to ``LDAPProps`` adapter.
  [rnix]

- Remove ``check_duplicates`` setting which is not available any more in
  node.ext.ldap.
  [rnix]

- Use node.ext.ldap 1.0b1.
  [rnix]

- major speedup expected by using node.ext.ldap >=1.0a1
  [jensens]

- use implementer decorator for better readability.
  [jensens]

- Fix setuptools to v7.0.
  [jensens]


1.4.0 (2014-10-24)
------------------

- Feature: Alternative volatile cache for UGM tree on plugin.
  [jensens]

- overhaul test setup
  [jensens]

- introduce pluggable caching mechanism on ugm-tree level, defaults to
  caching on request. Can be overruled by providing an adapter implementing
  ``pas.plugins.ldap.interfaces.IPluginCacheHandler``.
  [jensens]

- log how long it takes to build up a users or groups tree.
  [jensens]

1.3.2 (2014-09-10)
------------------

- Small fixes in inspector.
  [rnix]


1.3.1 (2014-08-05)
------------------

- Fix dependency versions.
  [rnix]


1.3.0 (2014-05-12)
------------------

- Raise ``RuntimeError`` instead of ``KeyError`` when password change method
  couldn't locate the user in LDAP tree. Maybe it's a local user and
  ``Products.PlonePAS.pas.userSetPassword`` expects a ``RuntimeError`` to be
  raised in this case.
  [saily]


1.2.0 (2014-03-13)
------------------

- add property ``check_duplicates``. Adds ability to disable duplicates check
  for keys in ldap in order to avoid failure if ldap strcuture is not perfect.

- Add new property to disable duplicate primary/secondary key checking
  in LDAP trees. This allows pas.plugins.ldap to read LDAP tree and ignore
  duplicated items instead of raising::

    Traceback (most recent call last):
    ...
    RuntimeError: Key not unique: <key>='<value>'.


1.1.0 (2014-03-03)
------------------

- ldap errors dont block that much if ldap is not reachable,
  timeout blocked in past the whole zope. now default timeout for retry is
  300s - and some code cleanup
  [jensens]

- use more modern base for testing
  [jensens]

- Add URL example to widget help information how to specify an ldap uri.
  [saily]

- Add new bootstrap v2
  [saily]


1.0.2
-----

- sometimes ldap returns an empty string as portrait. take this as no portrait.
  [jensens, 2013-09-11]

1.0.1
-----

- because of passwordreset problem we figured out that pas searchUsers calls
  plugins search with both login and name, which was passed to ugm and returned
  always an empty result
  [benniboy]

1.0
---

- make it work.

- base work done so far in ``bda.pasldap`` and ``bda.plone.ldap`` was merged.
