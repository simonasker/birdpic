from setuptools import setup
import py2exe

DATA_FILES = [
    ('', [
        'dll/libiomp5md.dll',
        'dll/mkl_core.dll',
        'dll/mkl_def.dll',
        'dll/mkl_intel_thread.dll',
        # Only one of _def and _mc seem to be needed
        # 'dll/mkl_mc.dll',
    ]),
    ('data', [
        'data/plumreg.csv',
        'data/ioc.xml',
    ]),
]

setup(
    name='DigBird',
    version='0.1',
    author='Simon Andersson',
    author_email='simon.asker@gmail.com',
    options={
        'py2exe': {
            'includes': [
                'matplotlib.backends.backend_tkagg',
                'scipy.linalg.cython_blas',
                'scipy.linalg.cython_lapack',
                'scipy.sparse.csgraph._validation',
                'tkinter.filedialog',
            ],
        },
    },
    data_files=DATA_FILES,
    windows=['main.py'],
)
