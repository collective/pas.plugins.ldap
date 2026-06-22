"""Import and export handlers for LDAP settings in Plone's control panel."""

from BTrees.OOBTree import OOBTree
from pas.plugins.ldap import PACKAGE_NAME
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.utils import XMLAdapterBase
from zope.component import queryMultiAdapter
from zope.interface import implementer


def _get_import_export_handler(context):
    """Get the import/export handler for LDAP settings.

    Args:
        context (object): The context providing access to the site and logging.

    Returns:
        IBody: The import/export handler for LDAP settings, or None
        if not found.
    """
    # get the acl_users from the site
    aclu = context.getSite().acl_users
    logger = context.getLogger(PACKAGE_NAME)
    # check if the LDAP plugin is installed
    if "pasldap" not in aclu.objectIds():
        return
    pasldap = aclu.pasldap
    handler = queryMultiAdapter((pasldap, context), IBody)
    if handler is not None:
        handler.filename = f"{handler.name}{handler.suffix}"
        return handler
    logger.warning("Can't find handler for ldap settings")


def import_settings(context):
    """Import LDAP settings from an XML file.

    Args:
        context (object): The import context, which provides access
        to the site and logging.
    """
    logger = context.getLogger(PACKAGE_NAME)
    handler = _get_import_export_handler(context)
    if not handler:
        return
    body = context.readDataFile(handler.filename)
    if body is None:
        return
    handler.body = body
    logger.info("Imported ldap settings.")


def export_settings(context):
    """Export LDAP settings to an XML file.

    Args:
        context (object): The export context, which provides access
        to the site and logging.
    """
    handler = _get_import_export_handler(context)
    if not handler:
        return
    body = handler.body
    if body is None:
        logger = context.getLogger(PACKAGE_NAME)
        logger.warning("Problem to get ldap settings.")
        return
    context.writeDataFile(handler.filename, body, handler.mime_type)


@implementer(IBody)
class LDAPPluginXMLAdapter(XMLAdapterBase):
    """Import PAS groups from LDAP config."""

    name = "ldapsettings"

    def _exportNode(self):
        """Export LDAP settings to an XML node.

        Returns:
            xml.dom.minidom.Element: The XML node representing
            the LDAP settings.
        """
        node = self._getObjectNode("object")
        self._setDataAndType(self.context.settings, node)
        return node

    def _importNode(self, node):
        """Import LDAP settings from an XML node."""
        data = self._getDataByType(node)
        if not data:
            self._logger.error("data is empty")
            return
        for key in data:
            self.context.settings[key] = data[key]

    def _setDataAndType(self, data, node):
        """Set the data and type attributes for an XML node.

        Args:
            data (any): The data to be set.
            node (xml.dom.minidom.Element): The XML node to set the data on.
        """
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
                f"Invalid type {type(data):s} found for key {data:s} on export, skipped."
            )
            return
        child = self._doc.createTextNode(data)
        node.appendChild(child)

    def _getDataByType(self, node):
        """Get the data from an XML node based on its type attribute."""
        vtype = node.getAttribute("type")
        if vtype == "list":
            data = []
            for element in node.childNodes:
                if element.nodeName != "element":
                    continue
                data.append(self._getDataByType(element))
            return data
        if vtype == "dict":
            data = {}
            for element in node.childNodes:
                if element.nodeName != "element":
                    continue
                key = element.getAttribute("key")
                if key is None:
                    self._logger.warning("No key found for dict on import, skipped.")
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
            self._logger.warning(f"Invalid type {vtype:s} found on import, skipped.")
            data = None
        return data
