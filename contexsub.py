__author__ = 'davbr'
import os
import sys
from xmlrpc.client import ServerProxy, Error
from oshash import hashFile
from urllib.request import urlretrieve
from zipfile import ZipFile
import configparser


class OsSession(ServerProxy):
    def __init__(self, address, key, username="", password="", lang="en"):
        super(OsSession, self).__init__(address)
        login = self.LogIn(username, password, lang, key)
        if login["status"] != "200 OK":
            raise login["status"]
        else:
            self.token = login["token"]

    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        self.LogOut(self.token)

class Movie:
    def __init__(self, filename):
        self.filename = filename
        self.size = os.path.getsize(filename)
        self.hash = hashFile(filename)




if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.dirname(sys.argv[0])+"\\contexsub.cfg")
    movie = Movie(sys.argv[1])
    moviedetails = {"moviehash": movie.hash, "moviesize": movie.size, "sublanguageid": config["DEFAULT"]["language"]}
    query = [moviedetails, {"limit": 1}]
    key = config["DEFAULT"]["key"]
    address = config["DEFAULT"]["address"]
    with OsSession(address, key) as subserver:
      subs = subserver.SearchSubtitles(subserver.token, query)["data"][0]
    zipsub = ZipFile(urlretrieve(subs["ZipDownloadLink"])[0])
    fname = zipsub.extract(subs["SubFileName"], os.path.dirname(movie.filename))
    os.rename(fname, movie.filename + ".srt")





