#!/usr/bin/env python
from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='junit-xml',
    author='Brian Beyer',
    author_email='brian@kyr.us',
    maintainer='Chad Hutchins',
    maintainer_email='chad@hutchins.house', 
    url='https://github.com/chadhutchins182/python-junit-xml',
    license='MIT',
    packages=find_packages(),
    test_suite='test_junit_xml',
    description='Creates JUnit XML test result documents that can be read by '
                'tools such as Atlassian Bamboo or Jenkins',
    long_description=read('README.md'),
    version='1.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: Freely Distributable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Testing',
        ],
    install_requires=[
        'six'
        ]
    )
