# -*- coding: utf-8 -*-
from node.ext.ldap.scope import ONELEVEL


DEFAULTS = {
    'server.uri': 'ldap://127.0.0.1:12345',
    'server.user': 'cn=Manager,ou=organizational-unit,dc=my-domain,dc=com',
    'server.password': 'secret',
    'server.ignore_cert': False,
    'server.start_tls': False,
    'server.page_size': 1000,

    'cache.cache': False,
    'cache.memcached': '127.0.0.1:11211',
    'cache.timeout': 300,  # seconds

    'users.baseDN': 'ou=users,dc=my-domain,dc=com',
    'users.attrmap': {
        'rdn': 'uid',
        'id': 'uid',
        'login': 'uid',
        'fullname': 'cn',
        'email': 'mail',
        'location': 'l'
    },
    'users.scope': ONELEVEL,
    'users.queryFilter': '(objectClass=inetOrgPerson)',
    'users.objectClasses': ['inetOrgPerson'],
    'users.defaults': {},
    'users.memberOfSupport': False,
    'users.account_expiration': False,
    'users.expires_attr': 'shadowExpire',
    'users.expires_unit': 0,

    'groups.baseDN': 'ou=groups,dc=my-domain,dc=com',
    'groups.attrmap': {
        'rdn': 'cn',
        'id': 'cn',
        'title': 'o',
        'description': 'description'
    },
    'groups.scope': ONELEVEL,
    'groups.queryFilter': '(objectClass=groupOfNames)',
    'groups.objectClasses': ['groupOfNames'],
    'groups.defaults': {},
    'groups.memberOfSupport': False,
    'groups.expires_attr': 'unused',
    'groups.expires_unit': 0,
}
