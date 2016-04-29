import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': [
        'matplotlib.backends.backend_tkagg',
        'tkinter',
    ],
    'include_msvcr': True,
}

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name='birdpic',
    version='0.1',
    description='Fooo',
    options={
        'build_exe': build_exe_options,
    },
    executables=[Executable('main.py', base=base)],
)
