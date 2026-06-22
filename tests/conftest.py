from pytest_plone import fixtures_factory
from testing import PASLDAP_FIXTURE


pytest_plugins = ["pytest_plone"]


globals().update(fixtures_factory(((PASLDAP_FIXTURE, "ldap"),)))
