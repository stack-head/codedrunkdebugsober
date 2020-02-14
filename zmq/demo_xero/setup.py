#!/usr/bin/env python3
import sys
from setuptools import setup, find_packages

# Pip will provide a version of this function, but pulling in pip in setup.py breeds problems
# in bitbake.  We can parse out requirements.txt here.
def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

requirements_file_path = 'requirements.txt'
test_requirements_file_path = 'test_requirements.txt'

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements(requirements_file_path)
test_install_reqs = parse_requirements(test_requirements_file_path)

# pytest-runner uses setup_requires.  By default, that means pytest-runner will install itself
# on any invocation of setup.py.  We don't want this, especially for building debian packages
# or other production stuff.  This checks arguments passed into setup.py call, and then
# only conditionally adds pytest_runner to setup.py.
# Note: this can be important-I've seen pytest dependency requirements outrun what
# debian or bitbake publishes, which screws us up when generating debian/bitbake builds.
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

setup(name='demo_xero',
      version='1.0',
      scripts=['./bin/demo_xerouniclient', './bin/demo_xerouniworker',
      			'./bin/demo_xerouniworker_emitter'],
      packages=find_packages(exclude=['*test*']),
      install_requires=install_reqs,
      setup_requires=pytest_runner,
      tests_require=test_install_reqs,
)
