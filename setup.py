import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="junit-xml",
    author="Tikani",
    author_email="",
    url="https://github.com/gitiJumi/python-junit-xml",
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    description="Creates JUnit XML test result documents that can be read by tools such as Jenkins",
    long_description=read("README.rst"),
    version="2.2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Freely Distributable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.8",
)
