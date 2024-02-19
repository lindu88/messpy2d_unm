import os
import PySide6
print(os.environ['QT_API'])
os.environ['QT_API'] = 'pyside6'
import qasync
from MessPy.MessPy2D import start_app


start_app()
