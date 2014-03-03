
History
=======

1.1.1 (unreleased)
------------------

- Nothing changed yet.


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
