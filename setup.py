from distutils.core import setup

setup(
    name='MessPy2d',
    version='1.0',
    packages=['Plans'],
    url='',
    requires=['qtpy', 'qtawesome', 'nicelib', ''numba',
              'formlayout', 'pyqtgraph', 'pytest', 'wrapt',
              'enaml', 'qasync'],
    license='BSD',
    author='Tillsten',
    author_email='mail.till@gmx.de',
    description='Ultrafast Spectroscopy Data Acquisition',
)
