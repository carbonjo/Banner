
from setuptools import setup, find_packages

setup(
    name='banner',
    version='0.1.0',
    url='https://github.com/<your-github-username>/banner',
    author='Joaquin Carbonara',
    author_email='joaquin.o.carbonara@gmail.com',
    description='Tools to facilitate access to Banner',
    packages=find_packages(),    
    install_requires=['pandas', 'selenium==4.11.2'],
)
