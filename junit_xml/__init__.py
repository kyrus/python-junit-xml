#!/usr/bin/env python
import sys, re
import xml.etree.ElementTree as ET
import xml.dom.minidom

"""
Based on the following understanding of what Jenkins can parse for JUnit XML files.

<?xml version="1.0" encoding="utf-8"?>
<testsuites errors="1" failures="1" tests="4" time="45">
    <testsuite errors="1" failures="1" hostname="localhost" id="0" name="base_test_1"
               package="testdb" tests="4" timestamp="2012-11-15T01:02:29">
        <properties>
            <property name="assert-passed" value="1"/>
        </properties>
        <testcase classname="testdb.directory" name="001-passed-test" time="10"/>
        <testcase classname="testdb.directory" name="002-failed-test" time="20">
            <failure message="Assertion FAILED: some failed assert" type="failure">
                the output of the testcase
            </failure>
        </testcase>
        <testcase classname="package.directory" name="003-errord-test" time="15">
            <error message="Assertion ERROR: some error assert" type="error">
                the output of the testcase
            </error>
        </testcase>
	<testcase classname="package.directory" name="003-skipped-test" time="0">
	    <skipped message="SKIPPED Test" type="skipped">
                the output of the testcase
            </skipped>	
	</testcase>
        <testcase classname="testdb.directory" name="003-passed-test" time="10">
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


class TestSuite(object):
    """Suite of test cases"""

    def __init__(self, name, test_cases=None, hostname=None, id=None,\
                 package=None, timestamp=None, properties=None):
        self.name = name
        if not test_cases:
            test_cases = []
        try:
            iter(test_cases)
        except TypeError:
            raise Exception('test_cases must be a list of test cases')
        self.test_cases = test_cases
        self.hostname = hostname
        self.id = id
        self.package = package
        self.timestamp = timestamp
        self.properties = properties

    def build_xml_doc(self):
        """Builds the XML document for the JUnit test suite"""
        # build the test suite element
        test_suite_attributes = dict()
        test_suite_attributes['name'] = str(self.name)
        test_suite_attributes['failures'] = str(len([c for c in self.test_cases if c.is_failure()]))
        test_suite_attributes['errors'] = str(len([c for c in self.test_cases if c.is_error()]))
	test_suite_attributes['skipped'] = str(len([c for c in self.test_cases if c.is_skipped()]))
        test_suite_attributes['time'] = str(sum(c.elapsed_sec for c in self.test_cases if c.elapsed_sec))        
        test_suite_attributes['tests'] = str(len(self.test_cases))

        if self.hostname:
            test_suite_attributes['hostname'] = str(self.hostname)
        if self.id:
            test_suite_attributes['id'] = str(self.id)
        if self.package:
            test_suite_attributes['package'] = str(self.package)
        if self.timestamp:
            test_suite_attributes['timestamp'] = str(self.timestamp)

        xml_element = ET.Element("testsuite", test_suite_attributes)

        # add any properties
        if self.properties:
            props_element = ET.SubElement(xml_element, "properties")
            for k, v in self.properties.items():
                attrs = {'name': str(k), 'value': str(v)}
                ET.SubElement(props_element, "property", attrs)

        # test cases
        for case in self.test_cases:
            test_case_attributes = dict()
            test_case_attributes['name'] = str(case.name)
            if case.elapsed_sec:
                test_case_attributes['time'] = "%f" % case.elapsed_sec
            if case.classname:
                test_case_attributes['classname'] = str(case.classname)

            test_case_element = ET.SubElement(xml_element, "testcase", test_case_attributes)

            # failures
            if case.is_failure():
                attrs = {'type': 'failure'}
                if case.failure_message:
                    attrs['message'] = case.failure_message
                failure_element = ET.Element("failure", attrs)
                if case.failure_output:
                    failure_element.text = case.failure_output
                test_case_element.append(failure_element)

            # errors
            if case.is_error():
                attrs = {'type': 'error'}
                if case.error_message:
                    attrs['message'] = case.error_message
                error_element = ET.Element("error", attrs)
                if case.error_output:
                    error_element.text = case.error_output
                test_case_element.append(error_element)

            # skippeds
            if case.is_skipped():
                attrs = {'type': 'skipped'}
                if case.skipped_message:
                    attrs['message'] = case.skipped_message
                skipped_element = ET.Element("skipped", attrs)
                if case.error_output:
                    skipped_element.text = case.skipped_output
                test_case_element.append(skipped_element)

            # test stdout
            if case.stdout:
                stdout_element = ET.Element("system-out")
                stdout_element.text = case.stdout
                test_case_element.append(stdout_element)

            # test stderr
            if case.stderr:
                stderr_element = ET.Element("system-err")
                stderr_element.text = case.stderr
                test_case_element.append(stderr_element)

        return xml_element

    @staticmethod
    def to_xml_string(test_suites, prettyprint=True, encoding=None):
        """Returns the string representation of the JUnit XML document"""
        try:
            iter(test_suites)
        except TypeError:
            raise Exception('test_suites must be a list of test suites')

        xml_element = ET.Element("testsuites")
        for ts in test_suites:
            xml_element.append(ts.build_xml_doc())

        xml_string = ET.tostring(xml_element, encoding=encoding)
        xml_string = TestSuite._clean_illegal_xml_chars(xml_string)

        if prettyprint:
            xml_string = xml.dom.minidom.parseString(xml_string).toprettyxml()
        return xml_string

    @staticmethod
    def to_file(file_descriptor, test_suites, prettyprint=True, encoding=None):
        """Writes the JUnit XML document to file"""
        file_descriptor.write(TestSuite.to_xml_string(test_suites, prettyprint, encoding))

    @staticmethod
    def _clean_illegal_xml_chars(string_to_clean):
        """Removes any illegal unicode characters from the given XML string"""
        # see http://stackoverflow.com/questions/1707890/fast-way-to-filter-illegal-xml-unicode-chars-in-python
        illegal_unichrs = [(0x00, 0x08), (0x0B, 0x1F), (0x7F, 0x84), (0x86, 0x9F),
                           (0xD800, 0xDFFF), (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
                           (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
                           (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                           (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
                           (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                           (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
                           (0x10FFFE, 0x10FFFF)]

        illegal_ranges = ["%s-%s" % (unichr(low), unichr(high))
                          for (low, high) in illegal_unichrs
                          if low < sys.maxunicode]

        illegal_xml_re = re.compile(u'[%s]' % u''.join(illegal_ranges))
        return illegal_xml_re.sub('', string_to_clean)


class TestCase(object):
    """A JUnit test case with a result and possibly some stdout or stderr"""

    def __init__(self, name, classname=None, elapsed_sec=None, stdout=None, stderr=None):
        self.name = name
        self.elapsed_sec = elapsed_sec
        self.stdout = stdout
        self.stderr = stderr
        self.classname = classname
        self.error_message = None
        self.error_output = None
        self.failure_message = None
        self.failure_output = None
        self.skipped_message = None
        self.skipped_output = None

    def add_error_info(self, message=None, output=None):
        """Adds an error message, output, or both to the test case"""
        if message:
            self.error_message = message
        if output:
            self.error_output = output

    def add_failure_info(self, message=None, output=None):
        """Adds a failure message, output, or both to the test case"""
        if message:
            self.failure_message = message
        if output:
            self.failure_output = output

    def add_skipped_info(self, message=None, output=None):
        """Adds a skipped message, output, or both to the test case"""
        if message:
            self.skipped_message = message
        if output:
            self.skipped_output = output

    def is_failure(self):
        """returns true if this test case is a failure"""
        return self.failure_output or self.failure_message

    def is_error(self):
        """returns true if this test case is an error"""
        return self.error_output or self.error_message

    def is_skipped(self):
        """returns true if this test case has been skipped"""
        return self.skipped_output or self.skipped_message
