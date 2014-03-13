
History
=======

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
