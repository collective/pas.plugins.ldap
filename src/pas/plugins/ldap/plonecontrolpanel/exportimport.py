# -*- coding: utf-8 -*-
from BTrees.OOBTree import OOBTree
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.utils import XMLAdapterBase
from zope.component import queryMultiAdapter
from zope.interface import implementer


def _get_import_export_handler(context):
    aclu = context.getSite().acl_users
    logger = context.getLogger("pas.plugins.ldap")
    if "pasldap" not in aclu.objectIds():
        return
    pasldap = aclu.pasldap
    handler = queryMultiAdapter((pasldap, context), IBody)
    if handler is not None:
        handler.filename = "%s%s" % (handler.name, handler.suffix)
        return handler
    logger.warning("Can't find handler for ldap settings")


def import_settings(context):
    logger = context.getLogger("pas.plugins.ldap")
    handler = _get_import_export_handler(context)
    if not handler:
        return
    body = context.readDataFile(handler.filename)
    if body is None:
        return
    handler.body = body
    logger.info("Imported ldap settings.")


def export_settings(context):
    handler = _get_import_export_handler(context)
    if not handler:
        return
    body = handler.body
    if body is None:
        logger = context.getLogger("pas.plugins.ldap")
        logger.warning("Problem to get ldap settings.")
        return
    context.writeDataFile(handler.filename, body, handler.mime_type)


@implementer(IBody)
class LDAPPluginXMLAdapter(XMLAdapterBase):
    """import pas groups from ldap config.
    """

    name = "ldapsettings"

    def _exportNode(self):
        node = self._getObjectNode("object")
        self._setDataAndType(self.context.settings, node)
        return node

    def _importNode(self, node):
        data = self._getDataByType(node)
        if not data:
            self._logger.error("data is empty")
            return
        for key in data:
            self.context.settings[key] = data[key]

    def _setDataAndType(self, data, node):
        if isinstance(data, (tuple, list)):
            node.setAttribute("type", "list")
            for value in data:
                element = self._doc.createElement("element")
                self._setDataAndType(value, element)
                node.appendChild(element)
            return
        if isinstance(data, (dict, OOBTree)):
            node.setAttribute("type", "dict")
            for key in sorted(data.keys()):
                element = self._doc.createElement("element")
                element.setAttribute("key", key)
                self._setDataAndType(data[key], element)
                node.appendChild(element)
            return
        if isinstance(data, bool):
            node.setAttribute("type", "bool")
            data = str(data)
        elif isinstance(data, int):
            node.setAttribute("type", "int")
            data = str(data)
        elif isinstance(data, float):
            node.setAttribute("type", "float")
            data = str(data)
        elif isinstance(data, (str,)):
            node.setAttribute("type", "string")
        else:
            self._logger.warning(
                "Invalid type {0:s} found for key {1:s} on export, skipped.".format(
                    type(data), data
                )
            )
            return
        child = self._doc.createTextNode(data)
        node.appendChild(child)

    def _getDataByType(self, node):
        vtype = node.getAttribute("type")
        if vtype == "list":
            data = list()
            for element in node.childNodes:
                if element.nodeName != "element":
                    continue
                data.append(self._getDataByType(element))
            return data
        if vtype == "dict":
            data = dict()
            for element in node.childNodes:
                if element.nodeName != "element":
                    continue
                key = element.getAttribute("key")
                if key is None:
                    self._logger.warning("No key found for dict on import, " "skipped.")
                    continue
                data.update({key: self._getDataByType(element)})
            return data
        data = self._getNodeText(node)
        if vtype == "bool":
            data = data.lower() == "true"
        elif vtype == "int":
            data = int(data)
        elif vtype == "float":
            data = float(data)
        elif vtype == "string":
            data = str(data)
        else:
            self._logger.warning(
                "Invalid type {0:s} found on import, skipped.".format(vtype)
            )
            data = None
        return data
