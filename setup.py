from setuptools import find_packages
from setuptools import setup

setup(
    name='gamms',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'pygame',
        'shapely',
        'networkx',
        'cbor2',
        'aenum',
        'osmnx',
    ],
)        