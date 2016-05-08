from setuptools import setup
# from distutils.core import setup
import py2exe


setup(
    name='DigBird',
    version='0.1',
    author='Simon Andersson',
    author_email='simon.asker@gmail.com',
    windows={
        'script': 'main.py',
    },
)
