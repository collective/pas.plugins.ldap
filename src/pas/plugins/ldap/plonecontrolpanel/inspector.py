# -*- coding: utf-8 -*-
from node.ext.ldap import LDAPNode
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPProps
from node.ext.ldap.interfaces import ILDAPUsersConfig
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from zope.component import getUtility

import json
import six


def safe_encode(val):
    if isinstance(val, six.text_type):
        return val.encode("utf-8")
    return val


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
        dn = self.request["dn"]
        base = self.request["base"]
        if base == "users":
            users = ILDAPUsersConfig(self.plugin)
            baseDN = users.baseDN
        else:
            groups = ILDAPGroupsConfig(self.plugin)
            baseDN = groups.baseDN
        root = LDAPNode(baseDN, self.props)
        node = root.node_by_dn(safe_unicode(dn), strict=True)
        ret = dict()
        for key, val in node.attrs.items():
            try:
                if not node.attrs.is_binary(key):
                    ret[safe_unicode(key)] = safe_unicode(val)
                else:
                    ret[safe_unicode(key)] = "(Binary Data with {0} Bytes)".format(
                        len(val)
                    )
            except UnicodeDecodeError:
                ret[safe_encode(key)] = "! (UnicodeDecodeError)"
            except Exception:
                ret[safe_encode(key)] = "! (Unknown Exception)"
        return json.dumps(ret)

    def children(self, baseDN):
        node = LDAPNode(baseDN, self.props)
        ret = list()
        # XXX: related search filters for users and groups container?
        for dn in node.search():
            ret.append({"dn": dn})
        return json.dumps(ret)
