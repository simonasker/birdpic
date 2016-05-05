from setuptools import setup


APP = ['main.py']
DATA_FILES = [('data', [
    'data/plumreg.csv',
])]
OPTIONS = {
    'argv_emulation': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
