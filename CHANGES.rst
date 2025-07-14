
History
=======


1.8.4 (2025-07-14)
------------------

- Remove the dependency from ``five.globalrequest``.
  This is needed to make this package work on Plone 6.1.2.
  See `PR #134 <https://github.com/collective/pas.plugins.ldap/pull/134>`_.
  [cillianderoiste]


1.8.3 (2024-11-13)
------------------

- Add uninstall profile
  [dumitval]
- Fix: use exact_match for searchUsers/searchGroups in getRolesForPrincipal/getPropertiesForUser
  to avoid unexpected results
  [mamico]


1.8.2 (2022-10-31)
------------------

- Add connection and operation timeout properties for LDAP server.
  Fixes `issue #61 <https://github.com/collective/pas.plugins.ldap/issues/61>`_.
  [mamico]


1.8.1 (2021-10-09)
------------------

- Fix imports for Zope 5 and Plone 6.
  [pbauer]


1.8.0 (2020-06-11)
------------------

Features:

- Support for nested groups in AD using LDAP_MATCHING_RULE_IN_CHAIN.
  [pbauer]

- Support for plugin-external group DNs when using memberOf attribute.
  [jensens]


1.7.2 (2020-02-21)
------------------

Bug fixes:

- Import loader from YAFOWIL.
  Fixes `issue #97 <https://github.com/collective/pas.plugins.ldap/issues/97>`_
  and `issue #92 <https://github.com/collective/pas.plugins.ldap/issues/92>`_.
  [al45tair]


1.7.1 (2020-02-14)
------------------

- Use the plugin ID as the property sheet ID instead of the user ID.
  Fixes `issue  #95 <https://github.com/collective/pas.plugins.ldap/issues/95>`_.
  [reinhardt]

- Grant the Member role to all LDAP users.
  [reinhardt]


1.7.0 (2020-01-22)
------------------

- Fixed error display for /plone_ldapcontrolpanel when a wrong value is
  provided for the "Groups container DN" field.
  [alecghica]

- Fixed error adding a Plone user group.
  [iulianpetchesi]

- Log LDAP-errors as level error, to get them i.e. into Sentry.
  [jensens]

- Make timeout of LDAP-errors logging configurable with environment variable ``PAS_PLUGINS_LDAP_ERROR_LOG_TIMEOUT``.
  [jensens]

- Log long running LDAP/ pas.plugin.ldap operations as error.
  Threshold can be controlled with environment variable ``PAS_PLUGINS_LDAP_LONG_RUNNING_LOG_THRESHOLD``.
  [jensens]


1.6.2 (2019-09-12)
------------------

- Remove broken old import step from base profile.
  Fixes `issue  #74 <https://github.com/collective/pas.plugins.ldap/issues/74>`_.
  [maurits]

- Remove deprecation warning for removal of time.clock() which will break
  Python 3.8 support.
  [fredvd]

- Require python-ldap 3.2.0. Fixes "initialize() got an unexpected keyword
  argument 'bytes_strictness'".
  [reinhardt]


1.6.1 (2019-05-07)
------------------

- Pimp ZMI view to look better on Zope 4.
  [jensens]

- Fixes #71, node.ext.ldap version-requirement wrong
  [jensens]


1.6.0 (2019-05-07)
------------------

- Fix inspector: In Python 3 JSON dumps does not accept bytes as keys.
  [jensens, 2silver]

- Explicitly set the ID on the property sheet instead of write on read.
  [jensens, 2silver]

- Less verbose plugin logging of pseudo errors.
  [jensens, 2silver]

- Enable partial search for users if no exact match was asked.
  [jensens]

- Add bundle on request for latest YAFOWIL.
  [jensens]

- Drop Plone 4.3 support.
  [jensens]

- Convert `plugin.py` doctests to unittests.
  [jensens]

- Black code style.
  [jensens]

- Fix #51: plone_ldapinspector broken with UnicodeDecodeError
  [dmunico]

- Make bind user and password optional.
  [thet, jensens]

- Python 3 support:

  - fixed imports
  - text/encoding fixes
  - fixed exception handling
  - mangled doctests using Py23DocChecker from node.ext.ldap
  - simplified object_classes expressions in yaml config

  [reinhardt]


1.5.3 (2017-12-15)
------------------

- Remove manual LDAP search pagination on UGM principal ``search`` calls.
  This is done in downstream API as of ``node.ext.ldap`` 1.0b7.
  [rnix]

- Fix testing: register plugin type of PlonePAS.
  [jensens, fredvd, mauritsvanrees]

- Overhaul of test setup (travis).
  [jensens]


1.5.2 (2017-10-20)
------------------

- Set the memcached TTW setting in the form definition to unicode, so that you
  can save the controlpanel form if you change this field.
  [fredvd]

- Improve README
  [svx]


1.5.1 (2016-10-18)
------------------

- Fix: TTW setting of ``page_size`` resulted in float value.
  Now set form datattype to integer.
  Thanks @datakurre for reporting!
  [jensens]


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
