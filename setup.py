from setuptools import setup

setup(
    name='PyTPG',
    version='0.96',
    packages=['tpg', 'tpg.configuration'],
    install_requires=['numba','numpy', 'unittest-xml-reporting','scipy'],
    license='MIT',
    description='Python implementation of Tangled Program Graphs.',
    long_description=open('README.md').read(),
    author='Ryan Amaral',
    author_email='ryan_amaral@live.com',
    url='https://github.com/Ryan-Amaral/PyTPG')
