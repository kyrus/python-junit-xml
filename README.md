python-junit-xml
================
[![Build Status](https://travis-ci.org/chadhutchins182/python-junit-xml.svg?branch=master)](https://travis-ci.org/chadhutchins182/python-junit-xml)

About
-----

A Python module for creating JUnit XML test result documents that can be
read by tools such as Atlassian Bamboo or Jenkins. 

Code originally forked from: https://github.com/kyrus/python-junit-xml

Installation
------------

Install using pip or easy_install:

```

	pip install junit-xml
	or
	easy_install junit-xml
```

You can also clone the Git repository from Github and install it manually:

```

    git clone https://github.com/kyrus/python-junit-xml.git
    python setup.py install
```

Using
-----

Create a test suite, add a test case, and print it to the screen:

```python

    from junit_xml import TestSuite, TestCase

    test_cases = [TestCase('Test1', 'some.class.name', 123.345, 'I am stdout!', 'I am stderr!')]
    ts = TestSuite("my test suite", test_cases)
    # pretty printing is on by default but can be disabled using prettyprint=False
    print(TestSuite.to_xml_string([ts]))
```

Produces the following output

```xml

    <?xml version="1.0" ?>
    <testsuites>
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
    </testsuites>
```

Writing XML to a file:

```python

    # you can also write the XML to a file and not pretty print it
    with open('output.xml', 'w') as f:
        TestSuite.to_file(f, [ts], prettyprint=False)

```
See the docs and unit tests for more examples.

NOTE: Unicode characters identified as "illegal or discouraged" are automatically
stripped from the XML string or file.

Running the tests
-----------------

```
    # activate your virtualenv
    pip install tox
    tox
```
