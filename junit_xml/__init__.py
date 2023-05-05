"""junit xml module
Based on the understanding of what Jenkins can parse for JUnit XML files.

<?xml version="1.0" encoding="utf-8"?>
<testsuites errors="1" failures="1" tests="4" time="45">
    <testsuite errors="1" failures="1" hostname="localhost" id="0" name="test1"
               package="testdb" tests="4" timestamp="2012-11-15T01:02:29">
        <properties>
            <property name="assert-passed" value="1"/>
        </properties>
        <testcase classname="testdb.directory" name="1-passed-test" time="10"/>
        <testcase classname="testdb.directory" name="2-failed-test" time="20">
            <failure message="Assertion FAILED: failed assert" type="failure">
                the output of the testcase
            </failure>
        </testcase>
        <testcase classname="package.directory" name="3-errord-test" time="15">
            <error message="Assertion ERROR: error assert" type="error">
                the output of the testcase
            </error>
        </testcase>
        <testcase classname="package.directory" name="3-skipped-test" time="0">
            <skipped message="SKIPPED Test" type="skipped">
                the output of the testcase
            </skipped>
        </testcase>
        <testcase classname="testdb.directory" name="3-passed-test" time="10">
            <system-out>
                I am system output
            </system-out>
            <system-err>
                I am the error output
            </system-err>
        </testcase>
    </testsuite>
</testsuites>
"""

import sys
import re
from typing import List
from xml.etree import ElementTree
import xml.dom.minidom

from junit_xml.root_element import TestSuite, build_xml_root


def to_xml_report_string(test_suites: List[TestSuite], prettyprint=True, encoding=None):
    """
    Returns the string representation of the JUnit XML document.
    @param test_suites: input for xml string generation
    @param prettyprint: flag to request formatted output, default=True
    @param encoding: The encoding of the input.
    @return: xml unicode string
    """
    xml_element = build_xml_root(test_suites)

    xml_string = ElementTree.tostring(xml_element, encoding=encoding)
    # is encoded now
    xml_string = clean_illegal_xml_chars(xml_string.decode(encoding or "utf-8"))
    # is unicode now

    if prettyprint:
        # minidom.parseString() works just on correctly encoded binary strings
        xml_string = xml_string.encode(encoding or "utf-8")
        xml_string = xml.dom.minidom.parseString(xml_string)
        # toprettyxml() produces unicode if no encoding is being passed
        # or binary string with an encoding
        xml_string = xml_string.toprettyxml(encoding=encoding)
        if encoding:
            xml_string = xml_string.decode(encoding)
        # is unicode now
    return xml_string


def clean_illegal_xml_chars(string_to_clean):
    """
    Removes any illegal unicode characters from the given XML string.

    @see: http://stackoverflow.com/questions/1707890/
    fast-way-to-filter-illegal-xml-unicode-chars-in-python
    """

    illegal_unichrs = [
        (0x00, 0x08),
        (0x0B, 0x1F),
        (0x7F, 0x84),
        (0x86, 0x9F),
        (0xD800, 0xDFFF),
        (0xFDD0, 0xFDDF),
        (0xFFFE, 0xFFFF),
        (0x1FFFE, 0x1FFFF),
        (0x2FFFE, 0x2FFFF),
        (0x3FFFE, 0x3FFFF),
        (0x4FFFE, 0x4FFFF),
        (0x5FFFE, 0x5FFFF),
        (0x6FFFE, 0x6FFFF),
        (0x7FFFE, 0x7FFFF),
        (0x8FFFE, 0x8FFFF),
        (0x9FFFE, 0x9FFFF),
        (0xAFFFE, 0xAFFFF),
        (0xBFFFE, 0xBFFFF),
        (0xCFFFE, 0xCFFFF),
        (0xDFFFE, 0xDFFFF),
        (0xEFFFE, 0xEFFFF),
        (0xFFFFE, 0xFFFFF),
        (0x10FFFE, 0x10FFFF),
    ]

    illegal_ranges = [
        f"{chr(low)}-{chr(high)}" for (low, high) in illegal_unichrs if low < sys.maxunicode
    ]

    joined = "".join(illegal_ranges)
    illegal_xml_re = re.compile(f"[{joined}]")
    return illegal_xml_re.sub("", string_to_clean)
