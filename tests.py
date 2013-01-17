from __future__ import with_statement
import unittest
import os
import tempfile
from xml.dom import minidom
from junit_xml import (TestCase, TestSuite)

"""Unit tests"""


def serialize_and_read(test_suites, to_file=False):
    """writes the test suite to an XML string and then re-reads it using minidom,
       returning => (test suite element, list of test case elements)"""
    try:
       iter(test_suites)
    except TypeError:
       test_suites = [test_suites]

    if to_file:
        fd, filename = tempfile.mkstemp(text=True)
        with os.fdopen(fd, 'w') as f:
            TestSuite.to_file(f, test_suites)
            
        print("Serialized XML to temp file [%s]" % filename)
        xmldoc = minidom.parse(filename)
        os.remove(filename)
    else:
        xml_string = TestSuite.to_xml_string(test_suites)
        print("Serialized XML to string:\n%s" % xml_string)
        xmldoc = minidom.parseString(xml_string)
    
    ret = []
    suites = xmldoc.getElementsByTagName("testsuites")[0]
    for suite in suites.getElementsByTagName("testsuite"):
        cases = suite.getElementsByTagName("testcase")
        ret.append((suite, cases))
    return ret

class TestSuiteTests(unittest.TestCase):
    def test_single_suite_to_file(self):
        (ts, tcs) = serialize_and_read(TestSuite('test', [TestCase('Test1')]), True)[0]
        verify_test_case(self, tcs[0], {'name':'Test1'})
        
    def test_multiple_suites_to_file(self):
        tss = [TestSuite('suite1', [TestCase('Test1')]), TestSuite('suite2', [TestCase('Test2')])]
        suites = serialize_and_read(tss, True)
        
        self.assertEqual('suite1', suites[0][0].attributes['name'].value)
        verify_test_case(self, suites[0][1][0], {'name':'Test1'})
        
        self.assertEqual('suite2', suites[1][0].attributes['name'].value)
        verify_test_case(self, suites[1][1][0], {'name':'Test2'})
        
    def test_multiple_suites_to_string(self):
        tss = [TestSuite('suite1', [TestCase('Test1')]), TestSuite('suite2', [TestCase('Test2')])]
        suites = serialize_and_read(tss)
        
        self.assertEqual('suite1', suites[0][0].attributes['name'].value)
        verify_test_case(self, suites[0][1][0], {'name':'Test1'})
        
        self.assertEqual('suite2', suites[1][0].attributes['name'].value)
        verify_test_case(self, suites[1][1][0], {'name':'Test2'})
        
    # TODO: add more tests for the other attributes and properties
        
class TestCaseTests(unittest.TestCase):
    def test_init(self):
        (ts, tcs) = serialize_and_read(TestSuite('test', [TestCase('Test1')]))[0]
        verify_test_case(self, tcs[0], {'name':'Test1'})
    
    def test_init_classname(self):
        (ts, tcs) = serialize_and_read(TestSuite('test', \
            [TestCase('Test1', 'some.class.name')]))[0]
        verify_test_case(self, tcs[0], {'name':'Test1', 'classname': 'some.class.name'})
    
    def test_init_classname_time(self):
        (ts, tcs) = serialize_and_read(TestSuite('test', \
            [TestCase('Test1', 'some.class.name', 123.345)]))[0]
        verify_test_case(self, tcs[0], {'name':'Test1', 'classname': 'some.class.name', 'time': ("%f" % 123.345)})
    
    def test_init_stderr(self):    
        (ts, tcs) = serialize_and_read(TestSuite('test', \
            [TestCase('Test1', 'some.class.name', 123.345, stderr='I am stderr!')]))[0]
        verify_test_case(self, tcs[0], {'name':'Test1', 'classname': 'some.class.name', 'time': ("%f" % 123.345)}, \
            stderr='I am stderr!')
    
    def test_init_stdout_stderr(self):    
        (ts, tcs) = serialize_and_read(TestSuite('test', \
            [TestCase('Test1', 'some.class.name', 123.345, 'I am stdout!', 'I am stderr!')]))[0]
        verify_test_case(self, tcs[0], {'name':'Test1', 'classname': 'some.class.name', 'time': ("%f" % 123.345)}, \
            stdout='I am stdout!', stderr='I am stderr!')
    
    def test_init_failure_message(self):
        tc = TestCase('Failure-Message')
        tc.add_failure_info("failure message")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(self, tcs[0], {'name':'Failure-Message'}, failure_message="failure message")
    
    def test_init_failure_output(self):
        tc = TestCase('Failure-Output')
        tc.add_failure_info(output="I failed!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(self, tcs[0], {'name':'Failure-Output'}, failure_output="I failed!")
    
    def test_init_failure(self):
        tc = TestCase('Failure-Message-and-Output')
        tc.add_failure_info("failure message", "I failed!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(self, tcs[0], {'name':'Failure-Message-and-Output'}, \
            failure_message="failure message", failure_output="I failed!")
    
    def test_init_error_message(self):
        tc = TestCase('Error-Message')
        tc.add_error_info("error message")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(self, tcs[0], {'name':'Error-Message'}, error_message="error message")
    
    def test_init_error_output(self):
        tc = TestCase('Error-Output')
        tc.add_error_info(output="I errored!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(self, tcs[0], {'name':'Error-Output'}, error_output="I errored!")
    
    def test_init_error(self):
        tc = TestCase('Error-Message-and-Output')
        tc.add_error_info("error message", "I errored!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(self, tcs[0], {'name':'Error-Message-and-Output'}, \
            error_message="error message", error_output="I errored!")

def verify_test_case(tc, test_case_element, expected_attributes, 
    error_message=None, error_output=None,
    failure_message=None, failure_output=None,
    stdout=None, stderr=None):

    for k, v in expected_attributes.iteritems():
        tc.assertEqual(v, test_case_element.attributes[k].value)
    
    for k in test_case_element.attributes.keys():
        tc.assertTrue(k in expected_attributes.keys())

        if stderr:
            tc.assertEqual(stderr, test_case_element.getElementsByTagName('system-err')[0].firstChild.nodeValue.strip())
        if stdout:
            tc.assertEqual(stdout, test_case_element.getElementsByTagName('system-out')[0].firstChild.nodeValue.strip())

        errors = test_case_element.getElementsByTagName('error')
        if error_message or error_output:
            tc.assertTrue(len(errors) > 0)
        else:
            tc.assertEqual(0, len(errors))
        
        if error_message:
            tc.assertEqual(error_message, errors[0].attributes['message'].value)

        if error_output:
            tc.assertEqual(error_output, errors[0].firstChild.nodeValue.strip())

        failures = test_case_element.getElementsByTagName('failure')
        if failure_message or failure_output:
            tc.assertTrue(len(failures) > 0)
        else:
            tc.assertEqual(0, len(failures))
        
        if failure_message:
            tc.assertEqual(failure_message, failures[0].attributes['message'].value)

        if failure_output:
            tc.assertEqual(failure_output, failures[0].firstChild.nodeValue.strip())
            
if __name__ == '__main__':
    unittest.main()
    