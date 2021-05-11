from setuptools import setup
import pathlib

thisdir = pathlib.Path(__file__).resolve().parent 
VERSION = thisdir.joinpath("VERSION").read_text().strip()

setup(
    name='wfchef',
    version=VERSION,
    author='Taina Coleman',
    author_email="tgcolema@usc.edu",
    packages=['wfchef'],
    install_requires=[
        'networkx',
        'stringcase'
    ],
    entry_points = {
        'console_scripts': [
            'wfchef-create-recipe=wfchef.chef:main',
            'wfchef-find-microstructures=wfchef.find_microstructures:main',
            'wfchef-duplicate=wfchef.duplicate:main',
        ],
    },
    url="https://github.com/tainagdcoleman/wfchef",
    download_url=f"https://github.com/tainagdcoleman/wfchef/archive/refs/tags/{VERSION}.tar.gz",
    keywords=["workflow", "wfcommons", "wf", "task", "graph", "generator"]
)