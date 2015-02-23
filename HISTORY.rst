
History
=======

1.4.1 (unreleased)
------------------

- Cache the expensive calls to ugm().users and ugm().groups, but drop caching
  on ugm() itself. Use ``plone.memoize`` as caching infrastructure, because of
  it's convenient caching decorators.
  [thet]

- use implementer decorator for better readability
  [jensens]

- Fix setuptools to v7.0
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
