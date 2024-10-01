# setup.py

from setuptools import setup, find_packages

setup(
    name='gziplogger',
    version='0.2.0',
    description='A logging utility package with gzip rotation and redirection of stdout/stderr',
    author='Anton Dovnar',
    author_email='anton.dovnar.tech@gmail.com',
    packages=find_packages(),
    install_requires=['requests'],
)
