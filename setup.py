from setuptools import setup

setup(
    name='wfchef',
    version='0.1.1',
    author='Taina Coleman',
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
            'wfchef-metric=wfchef.metric_wfchef:main',
            'wfhub-metric=wfchef.metric_wfhub:main',
            'wfchef-mse=wfchef.second_metric:main'

        ],
    }
)