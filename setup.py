from setuptools import setup, find_packages

setup(
    name = "timetracker",
    version = "1",
    packages = find_packages(),
    scripts = [ 'bin/tt' ],
)
