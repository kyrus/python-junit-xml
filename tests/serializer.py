import logging
from xml.dom import minidom

from junit_xml import to_xml_report_string

logger = logging.getLogger("Serializer")


def remove_blanks(node):
    for x in node.childNodes:
        if x.nodeType == minidom.Node.TEXT_NODE:
            if x.nodeValue:
                x.nodeValue = x.nodeValue.strip()
        elif x.nodeType == minidom.Node.ELEMENT_NODE:
            remove_blanks(x)


def read_testsuites_root(test_suites, prettyprint=False):
    """writes the test suite to an XML string and then re-reads it using minidom,
    returning => (test suite element, list of test case elements)"""
    if not isinstance(test_suites, list):
        test_suites = [test_suites]

    xml_string = to_xml_report_string(test_suites, prettyprint=prettyprint, encoding="utf-8")
    logger.debug("Serialized XML to string:\n%s", xml_string)

    xmldoc = minidom.parseString(xml_string)

    remove_blanks(xmldoc)
    xmldoc.normalize()

    return xmldoc.getElementsByTagName("testsuites")
