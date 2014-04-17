#!/usr/bin/env python
import os

try:
  from setuptools import setup
except:
  from distutils.core import setup

from muppet import __version__

readMeFile = open(os.path.join(os.path.dirname(__file__), "README.rst"))
long_description = readMeFile.read()
readMeFile.close()

setup(
  name="muppet",
  version=__version__,
  description="Durable messaging for distributed processing",
  long_description=long_description,
  url="https://github.com/pandastrike/muppet",
  author="Daniel Yoder, Mahesh Yellai",
  maintainer="Daniel Yoder, Mahesh Yellai",
  author_email="daniel.yoder@gmail.com, mahesh.yellai@gmail.com",
  maintainer_email="daniel.yoder@gmail.com, mahesh.yellai@gmail.com",
  keywords=["Durable messaging", "Distributed processing", "Redis"],
  license="MIT",
  packages=["muppet"],
  install_requires=["redis>=2.9.1"],
  tests_require=["pytest>=2.5.2"]
)