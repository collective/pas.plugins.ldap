# -*- coding: utf-8 -*-
import json
from node.utils import encode
from node.ext.ldap import LDAPNode
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from zope.component import getUtility
from Products.Five import BrowserView
from Products.CMFCore.interfaces import ISiteRoot


class LDAPInspector(BrowserView):

    @property
    def plugin(self):
        portal = getUtility(ISiteRoot)
        aclu = portal.acl_users
        plugin = aclu.pasldap
        return plugin

    @property
    def props(self):
        return ILDAPProps(self.plugin)

    def users_children(self):
        users = ILDAPUsersConfig(self.plugin)
        return self.children(users.baseDN)

    def groups_children(self):
        groups = ILDAPGroupsConfig(self.plugin)
        return self.children(groups.baseDN)

    def node_attributes(self):
        rdn = self.request['rdn']
        base = self.request['base']
        if base == 'users':
            users = ILDAPUsersConfig(self.plugin)
            baseDN = users.baseDN
        else:
            groups = ILDAPGroupsConfig(self.plugin)
            baseDN = groups.baseDN
        root = LDAPNode(baseDN, self.props)
        node = root[rdn]
        ret = dict()
        for key, val in node.attrs.items():
            try:
                if not node.attrs.is_binary(key):
                    ret[encode(key)] = encode(val)
                else:
                    ret[encode(key)] = "(Binary Data with %d Bytes)" % len(val)
            except UnicodeDecodeError, e:
                ret[key.encode('utf-8')] = '! (UnicodeDecodeError)'
            except Exception, e:
                ret[key.encode('utf-8')] = '! (Unknown Exception)'
        return json.dumps(ret)

    def children(self, baseDN):
        node = LDAPNode(baseDN, self.props)
        ret = list()
        for key in node:
            ret.append({'rdn': key})
        return json.dumps(ret)
