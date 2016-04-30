from distutils.core import setup
import py2exe

setup(
    windows=[{
        'script': 'main.py'
    }],
    options={
        'py2exe': {
            'includes': [
                'sip',
                'PyQt4.QtGui',
                'PyQt4.QtCore',
                'matplotlib.backends.backend_tkagg',
                'tkinter.filedialog',
            ],
        }
    },
)
