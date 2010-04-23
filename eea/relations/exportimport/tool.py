""" XML Adapter
"""
from zope import event
from zope.app import zapi
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.interfaces import IBody
from eea.relations.interfaces import IRelationsTool
from eea.relations.events import ObjectInitializedEvent
from eea.relations.interfaces import IFacetedNavigable

class RelationsToolXMLAdapter(XMLAdapterBase):
    """ Generic setup export/import xml adapter
    """
    __used_for__ = IRelationsTool

    def _exportBody(self):
        """Export the object as a file body.
        """
        self._doc.appendChild(self._exportNode())
        xml = self._doc.toprettyxml(' ', encoding='utf-8')
        self._doc.unlink()
        return xml
    body = property(_exportBody, XMLAdapterBase._importBody)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        for child in self.context.objectValues():
            exporter = zapi.queryMultiAdapter((child, self.environ), IBody)
            node.appendChild(exporter.node)
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        purge = node.getAttribute('purge')
        purge = self._convertToBoolean(purge)
        if purge:
            self.context.manage_delObjects(self.context.objectIds())

        for child in node.childNodes:
            if child.nodeName != 'object':
                continue

            purge_child = child.getAttribute('purge')
            purge_child = self._convertToBoolean(purge_child)
            name = child.getAttribute('name').encode('utf-8')
            obj_ids = self.context.objectIds()
            if (name in obj_ids) and purge_child:
                self.context.manage_delObjects([name,])
                continue

            obj = self.context._getOb(name, None)
            if not obj:
                portal_type = child.getAttribute('meta_type').encode('utf-8')
                name = self.context.invokeFactory(portal_type, name)
                obj = self.context._getOb(name)
                event.notify(ObjectInitializedEvent(obj))

            importer = zapi.queryMultiAdapter((obj, self.environ), IBody)
            importer.node = child

    node = property(_exportNode, _importNode)