# Copyright (c) 2006-2009 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL) 

import types
import os.path
from zope.app import zapi
from zope.interface import implements
from Acquisition import Implicit
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter


class PASGroupsFromLDAPConfigurationExportImport(Implicit):

    implements(IFilesystemExporter, IFilesystemImporter)

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter. """
        filename = os.path.join(subdir, '%s.xml' % self.context.getId())
        logger = export_context.getLogger('PASGroupsFromLDAP')

        exporter = zapi.queryMultiAdapter((self.context, export_context), IBody)
        if exporter is None:
            logger.warning('XML Export adapter missing.')
            return

        export_context.writeDataFile(filename, exporter.body, exporter.mime_type)
        
        
    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter. """        
        logger = import_context.getLogger('PASGroupsFromLDAP')
        filename = os.path.join(subdir, '%s.xml' % self.context.getId())
        body = import_context.readDataFile(filename, import_context.getEncoding())        
        importer = zapi.queryMultiAdapter((self.context, import_context), IBody)
        if importer is None:
            logger.warning('Import adapter missing.')
            return
        logger.info('PASGroupsFromLDAP plugin imported')


class PASGroupsFromLDAPXMLAdapter(XMLAdapterBase):
    """import pas groups from ldap config"""
    
    implements(IBody)

    def _exportNode(self):
        node = self._getObjectNode('object')
        self._setDataAndType(self.context.config, node)
        return node
                
    def _importNode(self, node):
        node = self._getObjectNode('object')        
        data = self._getDataFromNode(node)
        for key in data:
            if key in self.context.config:
               self.context.config[key] = data[key]
            
    def _setDataAndType(self, data, node):
        if isinstance(data, (tuple, list)):
            node.setAttribute('type', 'list')                
            for value in data:                    
                element = self._doc.createElement('element')
                self._setDataAndType(value, element)
                node.appendChild(element)
            return 
            
        if isinstance(data, (dict,)):
            node.setAttribute('type', 'dict')                
            for key in data.keys():                    
                element = self._doc.createElement('element')
                element.setAttribute('key', key)                
                self._setDataAndType(data[key], element)
                node.appendChild(element)
            return
            
        if type(data) is types.BooleanType:
            node.setAttribute('type', 'bool')                
            data = str(data)
        elif type(data) is types.IntType:
            node.setAttribute('type', 'int')                                    
            data = str(data)
        elif type(data) is types.FloatType:
            node.setAttribute('type', 'float')                                    
            data = str(data)
        elif type(data) in types.StringTypes:
            node.setAttribute('type', 'string')
        else:
            self._logger.warning('Invalid type %s found for key %s on export, skipped.' % (type(data), key))
            return
            
        child = self._doc.createTextNode(data)
        node.appendChild(child)
        
    def _getDataByType(self, node):
        vtype = node.getAttribute('type', None)
        if vtype is None:
            return None
        if vtype == 'list':
            data = list()
            for element in node.childNodes:
                if child.nodeName != 'element':
                    continue    
                data.append(self._getDataByType(element))
            return data
        if vtype == 'dict':
            data = dict()
            for element in node.childNodes:
                if child.nodeName != 'element':
                    continue 
                key =  element.getAttribute('key', None)  
                if key is None:
                    self._logger.warning('No key found for dict on import, skipped.')
                    return None
                data.update({key: self._getDataByType(element)})
                return data
        data = self._getNodeText(node)
        if vtype == 'bool':
            data = boolean(data)
        elif vtype == 'int':
            data = int(data)
        elif vtype == 'float':
            data = float(data)
        elif vtype == 'string':
            data = str(data)
        else:
            self._logger.warning('Invalid type %s found on import, skipped.' % vtype)
            return None