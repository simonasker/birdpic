from setuptools import setup


APP = ['main.py']
DATA_FILES = [('data', [
    'data/plumreg.csv',
    'data/ioc.xml',
])]
OPTIONS = {
    'argv_emulation': True,
}

setup(
    name='DigBird',
    version='0.1',
    author='Simon Andersson',
    author_email='simon.asker@gmail.com',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
