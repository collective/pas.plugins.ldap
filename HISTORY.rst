
History
=======

1.0.3 (unreleased)
------------------

- add property ``check_duplicates``. Adds ability to disable duplicates check
  for keys in ldap in order to avoid failure if ldap strcuture is not perfect.
  [jensens]

- Add URL example to widget help information how to specify an ldap uri.
  [saily]

- Add new bootstrap v1
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
