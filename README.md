python-junit-xml
================
[![Build Status](https://travis-ci.org/kyrus/python-junit-xml.png)](https://travis-ci.org/kyrus/python-junit-xml)

## About
A Python module for creating JUnit XML test result documents that can be
read by tools such as Jenkins. As there is no definitive source a Jenkins 
JUnit XSD that I could find, the supported schema was based on Google 
searches and the Jenkins JUnit XML reader source code. 

## Using
Install the module

    python setup.py install

Create a test suite, add a test case, and print it to the screen:

    from junit_xml import TestSuite, TestCase
    
    test_cases = [TestCase('Test1', 'some.class.name', 123.345, 'I am stdout!', 'I am stderr!')]
    ts = TestSuite("my test suite", test_cases)
    print(ts.to_xml_string())

Produces the following output (pretty printing is on by default but can be disabled using prettyprint=False)

    <?xml version="1.0" ?>
    <testsuite errors="0" failures="0" name="my test suite" tests="1">
        <testcase classname="some.class.name" name="Test1" time="123.345000">
            <system-out>
                I am stdout!
            </system-out>
            <system-err>
                I am stderr!
            </system-err>
        </testcase>
    </testsuite>

Writing XML to a file:

    # you can also write the XML to a file and not pretty print it
    with open('output.xml') as f:
		ts.write_to_file(f, prettyprint=False)

See the docs and unit tests for more examples.

## Running the tests

    python tests.py

