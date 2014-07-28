#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from xml.dom.minidom import parse as xml_dom_parse, getDOMImplementation, NodeList

class XmlFile(object):
    def __init__(self, filename=None, document_tag=None):
        self._filename = filename
        self._doc = None
        self._top_element = None
        self._last_error = None
        if filename is not None:
            self.open()
        elif document_tag is not None:
            self.new(document_tag)


    @staticmethod
    def getNodeText(node):
        rc = []
        for childnode in node.childNodes:
            if childnode.nodeType == node.TEXT_NODE:
                rc.append(childnode.data)
        return ''.join(rc)

    @staticmethod
    def setNodeText(node, text):
        # remove old text nodes
        for childnode in node.childNodes:
            if childnode.nodeType == node.TEXT_NODE:
                childnode.removeChild(node)
        childnode.appendChild(node.createTextNode(text))
    
    @staticmethod
    def getChildElementsByTagName(node, tagName):
        ret = NodeList()
        for childnode in node.childNodes:
            if childnode.nodeType == node.ELEMENT_NODE and \
                (tagName == "*" or childnode.tagName == tagName):
                ret.append(childnode)
        return ret

    @property
    def filename(self):
        return self._filename

    @property
    def last_error(self):
        return self._last_error

    @property
    def doc(self):
        return self._doc

    @property
    def root(self):
        return self._top_element

    def close(self):
        self._doc = None
        self._top_element = None
        self._last_error = None

    def open(self, filename=None):
        if filename is None:
            filename = self._filename
        try:
            f = open(filename, 'r')
            ret = True
        except IOError as e:
            self._last_error = str(e)
            f = None
            ret = False

        if ret:
            self._doc = xml_dom_parse(f)
            f.close()
            if self._doc is not None:
                self._top_element = self._doc.documentElement
                ret = True
            else:
                ret = False
        return ret

    def save(self, filename):
        if filename is None:
            filename = self._filename

        if self._doc is not None:
            try:
                f = open(filename, 'w')
                ret = True
            except IOError as e:
                self._last_error = str(e)
                f = None
                ret = False
            if ret:
                self._doc.writexml(f, indent="", addindent="    ", newl="\n")
                ret = True
                f.close()
        else:
            ret = False
        return ret
        
    def new(self, document_tag):
        impl = getDOMImplementation()
        self._doc = impl.createDocument(None, document_tag, None)
        self._top_element = self._doc.documentElement
