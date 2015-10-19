__author__ = 'davbr'
import os
import sys
from xmlrpc.client import ServerProxy, Error
from oshash import hashFile
from win32event import CreateMutex
if __name__ == "main":
    moviedetails = {"moviehash":hashFile(sys.argv[1]), "moviesize":os.path.getsize(sys.argv[1])}


