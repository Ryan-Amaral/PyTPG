from setuptools import setup, find_packages

setup(
    name='PyTPG',
    version='0.95',
    packages=find_packages(),
    install_requires=['numba','numpy'],
    license='MIT',
    description='Python implementation of Tangled Program Graphs.',
    long_description=open('README.md').read(),
    author='Ryan Amaral',
    author_email='ryan_amaral@live.com',
    url='https://github.com/Ryan-Amaral/PyTPG')
