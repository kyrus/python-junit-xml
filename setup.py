#!/usr/bin/env python
from setuptools import setup, find_packages
import os

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='junit_xml',
	author='Brian Beyer',
	author_email='brianebeyer@gmail.com',
	url='https://github.com/kyrus/python-junit-xml',
	packages=find_packages(),
	description=read('README.md'),
	long_description=read('README.md'),
	version = "0.1.0"
	)

