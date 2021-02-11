from setuptools import setup

setup(
    name='wfchef',
    version='0.1',
    author='Taina Coleman',
    packages=['wfchef'],
    install_requires=[
        'networkx',
        'stringcase'
    ],
    entry_points = {
        'console_scripts': ['wfchef=wfchef.chef:main'],
    }
)