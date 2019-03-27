from distutils.core import setup

setup(
    name='2D_IR',
    version='0.1',
    packages=['Plans'],
    url='',
    requires=['qtpy', 'qtawesome', 'nicelib', 'yamlcfg', 'formlayout', 'pyqtgraph', 'cffi'],
    license='BSD',
    author='Tillsten',
    author_email='mail.till@gmx.de',
    description='Ultrafast Spectroscopy Data Acquisition',
)
