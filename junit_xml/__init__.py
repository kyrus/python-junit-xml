#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import annotations
import warnings
from collections import defaultdict
import sys
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom

from six import u, iteritems, PY2

try:
    # Python 2
    unichr
except NameError:  # pragma: nocover
    # Python 3
    unichr = chr

"""
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


def decode(var, encoding):
    """
    If not already unicode, decode it.
    """
    if PY2:
        if isinstance(var, unicode):  # noqa: F821
            ret = var
        elif isinstance(var, str):
            if encoding:
                ret = var.decode(encoding)
            else:
                ret = unicode(var)  # noqa: F821
        else:
            ret = unicode(var)  # noqa: F821
    else:
        ret = str(var)
    return ret


class TestSuite(object):
    """
    Suite of test cases.
    Can handle unicode strings or binary strings if their encoding is provided.
    """

    def __init__(
        self,
        name,
        test_cases=None,
        test_suites=None,
        hostname=None,
        id=None,
        package=None,
        timestamp=None,
        properties=None,
        file=None,
        log=None,
        url=None,
        stdout=None,
        stderr=None,
    ):
        self.name = name
        self.tss_mode = False

        if not test_cases:
            test_cases = []

        if not test_suites:
            test_suites = []
        else:
            self.tss_mode = True
        try:
            iter(test_cases)
        except TypeError:
            raise TypeError("test_cases must be a list of test cases")

        try:
            iter(test_suites)
        except TypeError:
            raise TypeError("test_suites must be a list of test cases or test suites")

        self.test_cases = test_cases
        self.test_suites = test_suites
        self.timestamp = timestamp
        self.hostname = hostname
        self.id = id
        self.package = package
        self.file = file
        self.log = log
        self.url = url
        self.stdout = stdout
        self.stderr = stderr
        self.properties = properties

    @property
    def total_tests_disabled(self) -> int:
        """Gets total tests not enable of all test cases and test groups

        Returns:
            int: Total tests not enable in all test suite.
        """
        if self.tss_mode:
            return sum(ts.total_tests_disabled for ts in self.test_suites)
        return len([c for c in self.test_cases if not c.is_enabled])

    @property
    def total_tests_error(self) -> int:
        """Gets total tests with error of all test cases and test groups

        Returns:
            int: Total tests with error in all test suite.
        """
        if self.tss_mode:
            return sum(ts.total_tests_error for ts in self.test_suites)
        return len([c for c in self.test_cases if c.is_error()])

    @property
    def total_tests_failure(self) -> int:
        """Gets total tests failed of all test cases and test groups

        Returns:
            int: Total tests failed in all test suite.
        """
        if self.tss_mode:
            return sum(ts.total_tests_failure for ts in self.test_suites)
        return len([c for c in self.test_cases if c.is_failure()])

    @property
    def total_tests_skipped(self) -> int:
        """Gets total tests skipped of all test cases and test groups

        Returns:
            int: Total tests skipped in all test suite.
        """
        if self.tss_mode:
            return sum(ts.total_tests_skipped for ts in self.test_suites)
        return len([c for c in self.test_cases if c.is_skipped()])

    @property
    def total_tests(self) -> int:
        """Gets total tests of all test cases and test groups

        Returns:
            int: Total tests in all test suite.
        """
        if self.tss_mode:
            return sum(ts.total_tests for ts in self.test_suites)
        return len(self.test_cases)

    @property
    def total_time(self) -> int:
        """Gets total time of all test cases and test groups

        Returns:
            int: Total time in all test suite.
        """
        if self.tss_mode:
            return sum(ts.total_time for ts in self.test_suites)
        return sum(c.elapsed_sec for c in self.test_cases if c.elapsed_sec)

    def update_test_suite_attributes(self, ts: TestSuite, attributes: dict[str, str], encoding: str | None=None):
        """Updates test suite attributes according to self name, hostname, etc

        Args:
            ts (TestSuite): Test suite of attributes
            attributes (dict[str, str]): Attributes location dict.
            encoding (str | None, optional): Encoding, ex. "utf-8". Defaults to None.
        """
        attributes["name"] = decode(ts.name, encoding)

        if ts.hostname:
            attributes["hostname"] = decode(ts.hostname, encoding)
        if ts.id:
            attributes["id"] = decode(ts.id, encoding)
        if ts.package:
            attributes["package"] = decode(ts.package, encoding)
        if ts.timestamp:
            attributes["timestamp"] = decode(ts.timestamp, encoding)
        if ts.file:
            attributes["file"] = decode(ts.file, encoding)
        if ts.log:
            attributes["log"] = decode(ts.log, encoding)
        if ts.url:
            attributes["url"] = decode(ts.url, encoding)

    def get_test_suite_attributes(self, ts: TestSuite, ts_attributes: dict[str, str], encoding: str | None =None):
        """Adds all the test suite attributes

        Args:
            ts (TestSuite): Test suite to check for all the attributes
            ts_attributes (dict[str, str]): Dictionary destination of attributes
            encoding (str, optional): Enconding example "utf-8". Defaults to None.
        """
        self.update_test_suite_attributes(ts, ts_attributes, encoding)
        ts_attributes["disabled"] = str(ts.total_tests_disabled)
        ts_attributes["errors"] = str(ts.total_tests_error)
        ts_attributes["failures"] = str(ts.total_tests_failure)
        ts_attributes["skipped"] = str(ts.total_tests_skipped)
        ts_attributes["tests"] = str(ts.total_tests)
        ts_attributes["time"] = str(ts.total_time)

    def add_test_suite_when_testcases(self, ts: TestSuite, xml_element, encoding=None):
        # add any properties
        if ts.properties:
            props_element = ET.SubElement(xml_element, "properties")
            for k, v in ts.properties.items():
                attrs = {"name": decode(k, encoding), "value": decode(v, encoding)}
                ET.SubElement(props_element, "property", attrs)

        # add test suite stdout
        if ts.stdout:
            stdout_element = ET.SubElement(xml_element, "system-out")
            stdout_element.text = decode(ts.stdout, encoding)

        # add test suite stderr
        if ts.stderr:
            stderr_element = ET.SubElement(xml_element, "system-err")
            stderr_element.text = decode(ts.stderr, encoding)

        # test cases
        for case in ts.test_cases:
            test_case_attributes = dict()
            test_case_attributes["name"] = decode(case.name, encoding)
            if case.assertions:
                # Number of assertions in the test case
                test_case_attributes["assertions"] = "%d" % case.assertions
            if case.elapsed_sec:
                test_case_attributes["time"] = "%f" % case.elapsed_sec
            if case.timestamp:
                test_case_attributes["timestamp"] = decode(case.timestamp, encoding)
            if case.classname:
                test_case_attributes["classname"] = decode(case.classname, encoding)
            if case.status:
                test_case_attributes["status"] = decode(case.status, encoding)
            if case.category:
                test_case_attributes["class"] = decode(case.category, encoding)
            if case.file:
                test_case_attributes["file"] = decode(case.file, encoding)
            if case.line:
                test_case_attributes["line"] = decode(case.line, encoding)
            if case.log:
                test_case_attributes["log"] = decode(case.log, encoding)
            if case.url:
                test_case_attributes["url"] = decode(case.url, encoding)

            test_case_element = ET.SubElement(xml_element, "testcase", test_case_attributes)

            # failures
            for failure in case.failures:
                if failure["output"] or failure["message"]:
                    attrs = {"type": "failure"}
                    if failure["message"]:
                        attrs["message"] = decode(failure["message"], encoding)
                    if failure["type"]:
                        attrs["type"] = decode(failure["type"], encoding)
                    failure_element = ET.Element("failure", attrs)
                    if failure["output"]:
                        failure_element.text = decode(failure["output"], encoding)
                    test_case_element.append(failure_element)

            # errors
            for error in case.errors:
                if error["message"] or error["output"]:
                    attrs = {"type": "error"}
                    if error["message"]:
                        attrs["message"] = decode(error["message"], encoding)
                    if error["type"]:
                        attrs["type"] = decode(error["type"], encoding)
                    error_element = ET.Element("error", attrs)
                    if error["output"]:
                        error_element.text = decode(error["output"], encoding)
                    test_case_element.append(error_element)

            # skippeds
            for skipped in case.skipped:
                attrs = {"type": "skipped"}
                if skipped["message"]:
                    attrs["message"] = decode(skipped["message"], encoding)
                skipped_element = ET.Element("skipped", attrs)
                if skipped["output"]:
                    skipped_element.text = decode(skipped["output"], encoding)
                test_case_element.append(skipped_element)

            # test stdout
            if case.stdout:
                stdout_element = ET.Element("system-out")
                stdout_element.text = decode(case.stdout, encoding)
                test_case_element.append(stdout_element)

            # test stderr
            if case.stderr:
                stderr_element = ET.Element("system-err")
                stderr_element.text = decode(case.stderr, encoding)
                test_case_element.append(stderr_element)

    def get_testcases_xml_element(self, tss: list[TestSuite] | TestSuite, ts_xml, encoding=None) -> ET.Element:
        for ts in tss:
            if ts.tss_mode:
                ts_attributes = {}
                self.get_test_suite_attributes(ts, ts_attributes, encoding)

                new_testsuite = ET.Element("testsuite", ts_attributes)
                xml_element = self.get_testcases_xml_element(ts.test_suites, new_testsuite)
            else:
                test_suite_attributes = dict()
                test_cases = ts.test_cases
                if any(c.assertions for c in test_cases):
                    test_suite_attributes["assertions"] = str(sum([int(c.assertions) for c in test_cases if c.assertions]))
                test_suite_attributes["disabled"] = str(len([c for c in test_cases if not c.is_enabled]))
                test_suite_attributes["errors"] = str(len([c for c in test_cases if c.is_error()]))
                test_suite_attributes["failures"] = str(len([c for c in test_cases if c.is_failure()]))
                test_suite_attributes["skipped"] = str(len([c for c in test_cases if c.is_skipped()]))
                test_suite_attributes["tests"] = str(len(test_cases))
                test_suite_attributes["time"] = str(sum(c.elapsed_sec for c in test_cases if c.elapsed_sec))

                self.update_test_suite_attributes(ts, test_suite_attributes, encoding)

                xml_element = ET.Element("testsuite", test_suite_attributes)

                self.add_test_suite_when_testcases(ts, xml_element, encoding)

            ts_xml.append(xml_element)
        return ts_xml

    def build_xml_doc(self, encoding=None):
        """
        Builds the XML document for the JUnit test suite.
        Produces clean unicode strings and decodes non-unicode with the help of encoding.
        @param encoding: Used to decode encoded strings.
        @return: XML document with unicode string elements
        """

        # build the test suite element

        ts_attributes = {}
        self.get_test_suite_attributes(self, ts_attributes, encoding)

        ts_xml = ET.Element("testsuite", ts_attributes)
        xml_element = self.get_testcases_xml_element(self.test_suites, ts_xml, encoding)
        if len(self.test_suites) == 0:
            self.add_test_suite_when_testcases(self, xml_element, encoding)

        return xml_element

    @staticmethod
    def to_xml_string(test_suites, prettyprint=True, encoding=None):
        """
        Returns the string representation of the JUnit XML document.
        @param encoding: The encoding of the input.
        @return: unicode string
        """
        warnings.warn(
            "Testsuite.to_xml_string is deprecated. It will be removed in version 2.0.0. "
            "Use function to_xml_report_string",
            DeprecationWarning,
        )
        return to_xml_report_string(test_suites, prettyprint, encoding)

    @staticmethod
    def to_file(file_descriptor, test_suites, prettyprint=True, encoding=None):
        """
        Writes the JUnit XML document to a file.
        """
        warnings.warn(
            "Testsuite.to_file is deprecated. It will be removed in version 2.0.0. Use function to_xml_report_file",
            DeprecationWarning,
        )
        to_xml_report_file(file_descriptor, test_suites, prettyprint, encoding)

def pprint_xml(xml_element, encoding="utf-8"):
    xml_string = ET.tostring(xml_element, encoding=encoding)
    # is encoded now
    xml_string = _clean_illegal_xml_chars(xml_string.decode(encoding or "utf-8"))
    # is unicode now

    # minidom.parseString() works just on correctly encoded binary strings
    xml_string = xml_string.encode(encoding or "utf-8")
    xml_string = xml.dom.minidom.parseString(xml_string)
    # toprettyxml() produces unicode if no encoding is being passed or binary string with an encoding
    xml_string = xml_string.toprettyxml(encoding=encoding)
    if encoding:
        xml_string = xml_string.decode(encoding)
    print(xml_string)

def to_xml_report_string(test_suites, prettyprint=True, encoding=None):
    """
    Returns the string representation of the JUnit XML document.
    @param encoding: The encoding of the input.
    @return: unicode string
    """

    try:
        iter(test_suites)
    except TypeError:
        raise TypeError("test_suites must be a list of test suites")

    xml_element = ET.Element("testsuites")
    attributes = defaultdict(int)
    for ts in test_suites:
        ts_xml = ts.build_xml_doc(encoding=encoding)
        for key in ["disabled", "errors", "failures", "tests"]:
            attributes[key] += int(ts_xml.get(key, 0))
        for key in ["time"]:
            attributes[key] += float(ts_xml.get(key, 0))
        xml_element.append(ts_xml)
    for key, value in iteritems(attributes):
        xml_element.set(key, str(value))

    xml_string = ET.tostring(xml_element, encoding=encoding)
    # is encoded now
    xml_string = _clean_illegal_xml_chars(xml_string.decode(encoding or "utf-8"))
    # is unicode now

    if prettyprint:
        # minidom.parseString() works just on correctly encoded binary strings
        xml_string = xml_string.encode(encoding or "utf-8")
        xml_string = xml.dom.minidom.parseString(xml_string)
        # toprettyxml() produces unicode if no encoding is being passed or binary string with an encoding
        xml_string = xml_string.toprettyxml(encoding=encoding)
        if encoding:
            xml_string = xml_string.decode(encoding)
        # is unicode now
    return xml_string


def to_xml_report_file(file_descriptor, test_suites, prettyprint=True, encoding=None):
    """
    Writes the JUnit XML document to a file.
    """
    xml_string = to_xml_report_string(test_suites, prettyprint=prettyprint, encoding=encoding)
    # has problems with encoded str with non-ASCII (non-default-encoding) characters!
    file_descriptor.write(xml_string)


def _clean_illegal_xml_chars(string_to_clean):
    """
    Removes any illegal unicode characters from the given XML string.

    @see: http://stackoverflow.com/questions/1707890/fast-way-to-filter-illegal-xml-unicode-chars-in-python
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

    illegal_ranges = ["%s-%s" % (unichr(low), unichr(high)) for (low, high) in illegal_unichrs if low < sys.maxunicode]

    illegal_xml_re = re.compile(u("[%s]") % u("").join(illegal_ranges))
    return illegal_xml_re.sub("", string_to_clean)


class TestCase(object):
    """A JUnit test case with a result and possibly some stdout or stderr"""

    def __init__(
        self,
        name,
        classname=None,
        elapsed_sec=None,
        stdout=None,
        stderr=None,
        assertions=None,
        timestamp=None,
        status=None,
        category=None,
        file=None,
        line=None,
        log=None,
        url=None,
        allow_multiple_subelements=False,
    ):
        self.name = name
        self.assertions = assertions
        self.elapsed_sec = elapsed_sec
        self.timestamp = timestamp
        self.classname = classname
        self.status = status
        self.category = category
        self.file = file
        self.line = line
        self.log = log
        self.url = url
        self.stdout = stdout
        self.stderr = stderr

        self.is_enabled = True
        self.errors = []
        self.failures = []
        self.skipped = []
        self.allow_multiple_subalements = allow_multiple_subelements

    def add_error_info(self, message=None, output=None, error_type=None):
        """Adds an error message, output, or both to the test case"""
        error = {}
        error["message"] = message
        error["output"] = output
        error["type"] = error_type
        if self.allow_multiple_subalements:
            if message or output:
                self.errors.append(error)
        elif not len(self.errors):
            self.errors.append(error)
        else:
            if message:
                self.errors[0]["message"] = message
            if output:
                self.errors[0]["output"] = output
            if error_type:
                self.errors[0]["type"] = error_type

    def add_failure_info(self, message=None, output=None, failure_type=None):
        """Adds a failure message, output, or both to the test case"""
        failure = {}
        failure["message"] = message
        failure["output"] = output
        failure["type"] = failure_type
        if self.allow_multiple_subalements:
            if message or output:
                self.failures.append(failure)
        elif not len(self.failures):
            self.failures.append(failure)
        else:
            if message:
                self.failures[0]["message"] = message
            if output:
                self.failures[0]["output"] = output
            if failure_type:
                self.failures[0]["type"] = failure_type

    def add_skipped_info(self, message=None, output=None):
        """Adds a skipped message, output, or both to the test case"""
        skipped = {}
        skipped["message"] = message
        skipped["output"] = output
        if self.allow_multiple_subalements:
            if message or output:
                self.skipped.append(skipped)
        elif not len(self.skipped):
            self.skipped.append(skipped)
        else:
            if message:
                self.skipped[0]["message"] = message
            if output:
                self.skipped[0]["output"] = output

    def is_failure(self):
        """returns true if this test case is a failure"""
        return sum(1 for f in self.failures if f["message"] or f["output"]) > 0

    def is_error(self):
        """returns true if this test case is an error"""
        return sum(1 for e in self.errors if e["message"] or e["output"]) > 0

    def is_skipped(self):
        """returns true if this test case has been skipped"""
        return len(self.skipped) > 0
