from distutils.core import setup
import py2exe

setup(console=['scmgr.py'],
      data_files = [(".", ["config.txt", "db.txt"])])
