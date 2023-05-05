# -*- coding: UTF-8 -*-

from unittest import mock

import pytest

from junit_xml import to_xml_report_string
from junit_xml.root_element import TestSuite
from junit_xml.single_entry import TestCase
from .serializer import read_testsuites_root

sample_testsuite_name = "suite"

sample_hostname = "localhost"
sample_id = 42

sample_property_entry = ("foo", "bar")
sample_package = "sample.mypackage"

sample_timestamp = 1398382805

suite_name_1 = "suite1"
testcase_name_1 = "Test1"

suite_name_2 = "suite2"
testcase_name_2 = "Test2"

sample_testcase_name = "SomeTest"
generated_timestamp = "2022-05-12T09:19:42"


def read_first_testsuite(test_suites, prettyprint=False):
    res = read_testsuites_root(test_suites, prettyprint)[0].getElementsByTagName("testsuite")[0]
    return res


def test_single_testsuite_wrong_testcase_type():
    with pytest.raises(TypeError) as exc_info:
        TestSuite("test", TestCase("Test1"))
        assert str(exc_info.value) == "test_cases must be a list of test cases"


def test_single_testsuite_no_testcases():
    ts = read_first_testsuite(
        TestSuite(
            name=sample_testsuite_name,
            test_cases=[],
            hostname=sample_hostname,
            properties={sample_property_entry[0]: sample_property_entry[1]},
            package=sample_package,
            timestamp=sample_timestamp,
        ),
        prettyprint=True,
    )

    assert ts.tagName == "testsuite"

    assert ts.attributes["name"].value == sample_testsuite_name
    assert ts.attributes["hostname"].value == sample_hostname

    assert ts.attributes["package"].value == sample_package
    assert ts.attributes["timestamp"].value == str(sample_timestamp)
    assert ts.childNodes[0].childNodes[0].attributes["name"].value == sample_property_entry[0]
    assert ts.childNodes[0].childNodes[0].attributes["value"].value == sample_property_entry[1]


exp_output_pretty_p = '<?xml version="1.0" encoding="utf-8"?>\n'
exp_output_pretty_p += '<testsuites tests="1" errors="0" failures="0" disabled="0" skipped="0" '
exp_output_pretty_p += 'time="0.000">\n'
exp_output_pretty_p += f'\t<testsuite name="{sample_testsuite_name}" disabled="0" errors="0" failures="0" skipped="0" '
exp_output_pretty_p += f'tests="1" time="0.000" id="42" timestamp="{generated_timestamp}">\n'
exp_output_pretty_p += f'\t\t<testcase name="{sample_testcase_name}"/>\n'
exp_output_pretty_p += '\t</testsuite>\n'
exp_output_pretty_p += '</testsuites>\n'

exp_output_no_pretty = '<testsuites tests="1" errors="0" failures="0" disabled="0" skipped="0" '
exp_output_no_pretty += f'time="0.000"><testsuite name="{sample_testsuite_name}" disabled="0" errors="0" failures="0" '
exp_output_no_pretty += 'skipped="0" tests="1" time="0.000" id="42" '
exp_output_no_pretty += f'timestamp="{generated_timestamp}"><testcase name="{sample_testcase_name}" '
exp_output_no_pretty += '/></testsuite></testsuites>'

expected_xml_string = '<?xml version="1.0" ?>\n'
expected_xml_string += '<testsuites tests="2" errors="0" failures="0" disabled="0" skipped="0" '
expected_xml_string += 'time="0.000">\n'
expected_xml_string += '\t<testsuite name="suite1" disabled="0" errors="0" failures="0" skipped="0" '
expected_xml_string += f'tests="1" time="0.000" id="1" timestamp="{generated_timestamp}">\n'
expected_xml_string += '\t\t<testcase name="Test1"/>\n'
expected_xml_string += '\t</testsuite>\n'
expected_xml_string += '\t<testsuite name="suite2" disabled="0" errors="0" failures="0" skipped="0" '
expected_xml_string += f'tests="1" time="0.000" id="1" timestamp="{generated_timestamp}">\n'
expected_xml_string += '\t\t<testcase name="Test2"/>\n'
expected_xml_string += '\t</testsuite>\n'
expected_xml_string += '</testsuites>\n'


@pytest.mark.parametrize("pretty_print, expected_output",
                         [(True, exp_output_pretty_p),
                          (False, exp_output_no_pretty)])
@mock.patch("junit_xml.root_element.get_new_id", create=True)
@mock.patch("junit_xml.root_element.get_current_timestamp", create=True)
def test_single_suite_with_prettyprint(time_provider_mock: mock.Mock, id_provider: mock.Mock,
                                       pretty_print, expected_output):
    time_provider_mock.return_value = generated_timestamp
    id_provider.return_value = "42"

    input_testsuite = TestSuite(sample_testsuite_name, [TestCase(sample_testcase_name)])

    act_output = to_xml_report_string([input_testsuite], prettyprint=pretty_print, encoding="utf-8")

    assert act_output == expected_output


@mock.patch("junit_xml.root_element.get_new_id", create=True)
@mock.patch("junit_xml.root_element.get_current_timestamp", create=True)
def test_to_xml_string(time_provider_mock: mock.Mock, id_provider: mock.Mock):
    time_provider_mock.return_value = generated_timestamp
    id_provider.return_value = "1"

    test_suites = [
        TestSuite(name="suite1", test_cases=[TestCase(name="Test1")]),
        TestSuite(name="suite2", test_cases=[TestCase(name="Test2")]),
    ]
    xml_string = to_xml_report_string(test_suites)

    assert xml_string == expected_xml_string


def test_attribute_disable():
    tc = TestCase("Disabled-Test")
    tc.is_enabled = False
    tss = [TestSuite(sample_testsuite_name, [tc])]
    # res = to_xml_report_string(tss)
    # print(f"\n{res}")
    suite = read_testsuites_root(tss)[0].getElementsByTagName("testsuite")

    assert suite[0].attributes["disabled"].value == "1"


def test_stdout_stderr():
    suite = read_first_testsuite(
        TestSuite(name=sample_testsuite_name, stdout="I am stdout!",
                  stderr="I am stderr!", test_cases=[TestCase(name=sample_testcase_name)])
    )
    assert suite.getElementsByTagName("system-err")[0].firstChild.data == "I am stderr!"
    assert suite.getElementsByTagName("system-out")[0].firstChild.data == "I am stdout!"


def test_no_assertions():
    suite = read_first_testsuite(
        TestSuite(name=sample_testsuite_name, test_cases=[TestCase(name=sample_testcase_name)]))
    assert not suite.getElementsByTagName("testcase")[0].hasAttribute("assertions")


def test_assertions():
    suite = read_first_testsuite(
        TestSuite(name=sample_testsuite_name,
                  test_cases=[TestCase(name=sample_testcase_name, assertions=5)]))

    assert suite.getElementsByTagName("testcase")[0].attributes["assertions"].value == "5"


def test_to_xml_string_wrong_input_type():
    test_suites = TestSuite(sample_testsuite_name, [TestCase(sample_testcase_name)])

    with pytest.raises(TypeError) as excinfo:
        to_xml_report_string(test_suites)
    assert str(excinfo.value) == "test_suites must be a list of test suites"
