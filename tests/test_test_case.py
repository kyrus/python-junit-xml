# -*- coding: UTF-8 -*-

import pytest

from junit_xml.root_element import TestSuite as Suite
from junit_xml.single_entry import TestCase as Case
from .serializer import read_testsuites_root

sample_testsuite_name = "Banane"

sample_testcase_name = "Test1"
sample_classname = "some.class.name"
sample_time = 123.345

sample_failure_msg = "failure message: something bad happened"
sample_failure_output = "I failed!"

sample_error_message = "error message"
sample_error_output = "I errored!"

sample_skipped_message = "skipped message"
sample_skipped_output = "I skipped!"


def read_testcases(test_suites, prettyprint=False):
    suites = read_testsuites_root(test_suites, prettyprint)[0]
    return suites.getElementsByTagName("testsuite")[0].getElementsByTagName("testcase")


@pytest.mark.parametrize("_input, expected_output",
                         [
                             (Case(sample_testcase_name),
                              {"name": sample_testcase_name}),

                             (Case(name=sample_testcase_name, classname=sample_classname),
                              {"name": sample_testcase_name, "classname": sample_classname}),

                             (Case(name=sample_testcase_name, classname=sample_classname,
                                   time=sample_time),
                              {"name": sample_testcase_name, "classname": sample_classname,
                               "time": "%.3f" % sample_time})
                         ])
def test_report_passing_test(_input, expected_output):
    test_case_element = read_testcases(Suite(sample_testsuite_name, [_input]))

    for _key, _value in expected_output.items():
        assert test_case_element[0].attributes[_key].value == _value, \
            f"key: {_key} value: {_value} vs. {test_case_element[0].attributes[_key].value}"

    for act_key in test_case_element[0].attributes.keys():
        assert act_key in expected_output.keys()

    _failures = test_case_element[0].getElementsByTagName("failure")
    _errors = test_case_element[0].getElementsByTagName("error")
    _skipped = test_case_element[0].getElementsByTagName("skipped")

    assert not _failures
    assert not _errors
    assert not _skipped


@pytest.mark.parametrize("_input_error_message,_input_error_output,_default_type,_error_type",
                         [(sample_error_message, sample_error_output, True, "error"),
                          (sample_error_message, sample_error_output, False, "com.example.Error")
                          ])
def test_error_message_and_output_default_error_type(_input_error_message, _input_error_output,
                                                     _default_type, _error_type):
    tc = Case(sample_testcase_name)
    if _default_type:
        tc.add_error_info(_input_error_message, _input_error_output)
    else:
        tc.add_error_info(_input_error_message, _input_error_output, _error_type)

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _errors = tcs[0].getElementsByTagName("error")
    assert _errors[0].attributes["message"].value == _input_error_message
    assert _errors[0].attributes["type"].value == _error_type
    assert _errors[0].firstChild.nodeValue.strip() == _input_error_output


def test_skipped_message_only():
    tc = Case(sample_testcase_name)

    tc.add_skipped_info(sample_skipped_message)

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _skipped = tcs[0].getElementsByTagName("skipped")
    assert _skipped[0].attributes["message"].value == sample_skipped_message
    assert _skipped[0].attributes["type"].value == "skipped"
    assert not _skipped[0].firstChild


def test_skipped_message_and_output():
    tc = Case(sample_testcase_name)
    tc.add_skipped_info(sample_skipped_message, sample_skipped_output)

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _skipped = tcs[0].getElementsByTagName("skipped")

    assert _skipped[0].attributes["message"].value == sample_skipped_message
    assert _skipped[0].attributes["type"].value == "skipped"
    assert _skipped[0].firstChild.nodeValue.strip() == sample_skipped_output


def test_mixed_skipped_and_err_output():
    tc = Case(sample_testcase_name)
    tc.add_skipped_info(output=sample_skipped_output)
    tc.add_error_info(output=sample_error_output)

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _skipped = tcs[0].getElementsByTagName("skipped")
    assert _skipped[0].firstChild.nodeValue.strip() == sample_skipped_output
    assert _skipped[0].attributes["type"].value == "skipped"

    _errors = tcs[0].getElementsByTagName("error")
    assert _errors[0].firstChild.nodeValue.strip() == sample_error_output
    assert _errors[0].attributes["type"].value == "error"


def test_multiple_errors():
    """Tests multiple errors in one test case"""
    tc = Case(sample_testcase_name, allow_multiple_subelements=True)
    tc.add_error_info(sample_error_message, sample_error_output)

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _errors = tcs[0].getElementsByTagName("error")
    assert _errors[0].attributes["message"].value == sample_error_message
    assert _errors[0].attributes["type"].value == "error"
    assert _errors[0].firstChild.nodeValue.strip() == sample_error_output

    error_entry = ("Second error message", "Second error output")
    tc.add_error_info(error_entry[0], error_entry[1])

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _errors = tcs[0].getElementsByTagName("error")
    assert len(_errors) == 2
    assert _errors[1].attributes["message"].value == error_entry[0]
    assert _errors[1].attributes["type"].value == "error"
    assert _errors[1].firstChild.nodeValue.strip() == error_entry[1]


def test_multiple_failures():
    """Tests multiple failures in one test case"""
    tc = Case(sample_testcase_name, allow_multiple_subelements=True)
    tc.add_failure_info(sample_failure_msg, sample_failure_output)

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _failures = tcs[0].getElementsByTagName("failure")
    assert _failures[0].attributes["message"].value == sample_failure_msg
    assert _failures[0].attributes["type"].value == "failure"
    assert _failures[0].firstChild.nodeValue.strip() == sample_failure_output

    second_failure_entry = ("Second failure message", "Second failure output")

    tc.add_failure_info(second_failure_entry[0], second_failure_entry[1])

    tcs = read_testcases(Suite(sample_testsuite_name, [tc]))

    _failures = tcs[0].getElementsByTagName("failure")
    assert len(_failures) == 2
    assert _failures[1].attributes["message"].value == second_failure_entry[0]
    assert _failures[1].attributes["type"].value == "failure"
    assert _failures[1].firstChild.nodeValue.strip() == second_failure_entry[1]


def test_multiple_skipped():
    """Tests multiple skipped messages in one test case"""
    testcase_under_test = Case(sample_testcase_name, allow_multiple_subelements=True)
    testcase_under_test.add_skipped_info(sample_skipped_message, sample_skipped_output)

    tcs = read_testcases(Suite(sample_testsuite_name, [testcase_under_test]))

    _skipped = tcs[0].getElementsByTagName("skipped")
    assert _skipped[0].firstChild.nodeValue.strip() == sample_skipped_output
    assert _skipped[0].attributes["message"].value == sample_skipped_message

    sample_skip_2 = ("Second skipped message", "Second skipped output")

    testcase_under_test.add_skipped_info(sample_skip_2[0], sample_skip_2[1])

    tcs = read_testcases(Suite(sample_testsuite_name, [testcase_under_test]))

    _skipped = tcs[0].getElementsByTagName("skipped")
    assert len(_skipped) == 2
    assert _skipped[1].firstChild.nodeValue.strip() == sample_skip_2[1]
    assert _skipped[1].attributes["message"].value == sample_skip_2[0]
