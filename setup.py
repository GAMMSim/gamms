from setuptools import find_packages
from setuptools import setup

setup(
    name='gamms',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pygame',
        'shapely',
        'networkx',
        'py-ubjson'
    ],
)        