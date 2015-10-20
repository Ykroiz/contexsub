__author__ = 'davbr'
import os
import sys
from xmlrpc.client import ServerProxy, Error
from oshash import hashFile
from urllib.request import urlretrieve
from zipfile import ZipFile
import configparser
from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS
from tkinter import *
import tkinter.messagebox
import gettext



APP_PATH = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
OS_LOGO = APP_PATH + "\\oslogo.gif"
CFG_FILE = APP_PATH + "\\contexsub.cfg"
LOCALE_PATH = APP_PATH + "\\locale\\"
OS_LINK = 'http://www.opensubtitles.org'
CFG_DEFAULT = {"key": "OSTestUserAgent",
               "address": "https://api.opensubtitles.org/xml-rpc",
               "language": "eng",
               "username": "",
               "password": ""}

gettext.bindtextdomain('contexsub', LOCALE_PATH)
gettext.textdomain('contexsub')
_ = gettext.gettext

class SubExceptions(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class OsSession(ServerProxy):
    def __init__(self, address, key, username="", password="", lang="en"):
        super(OsSession, self).__init__(address)
        login = self.LogIn(username, password, lang, key)
        if login["status"] != "200 OK":
            raise SubExceptions(login["status"], _("Login to OpenSubtitles failed"))
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



class SingleInstance:

    def __init__(self):
        self.mutexui = 'cxsmutex_{CA99EC98-5C30-4CB3-8F3C-818948AE81B9}'
        self.mutex = CreateMutex(None, False, self.mutexui)
        self.lasterror = GetLastError()

    def isrunning(self):
        return self.lasterror == ERROR_ALREADY_EXISTS

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)

class Conf(configparser.ConfigParser):
    def __init__(self, configfile, cfgdefaults, **kwargs):
        super(Conf, self).__init__()
        self.configfile = configfile
        if not os.path.exists(configfile):
            self['DEFAULT'] = cfgdefaults
            for key, value in kwargs.items():
                self[key] = value
            with open(configfile, 'w') as cfgfile:
                self.write(cfgfile)
        else:
            self.read(CFG_FILE)

    def guiconf(self):
        guifields={"DEFAULT": {}}
        root = Tk()

        def callback():
            nonlocal self
            for key in guifields["DEFAULT"]:
                self["DEFAULT"][key] = guifields["DEFAULT"][key].get()
            with open(self.configfile, 'w') as cfgfile:
                self.write(cfgfile)

        for key in self["DEFAULT"].keys():
            frame = Frame(root)
            frame.pack(side=TOP)
            Label(frame, text=key).pack(side=LEFT)
            guifields["DEFAULT"][key] = Entry(frame)
            guifields["DEFAULT"][key].insert(0, self["DEFAULT"][key])
            guifields["DEFAULT"][key].pack(side=LEFT)

        Button(root, text="Save", command=callback).pack(side=TOP)
        root.mainloop()




if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if sys.argv[1] == "config":
            config = Conf(CFG_FILE, CFG_DEFAULT)
            config.guiconf()
        else:
            cxs = SingleInstance()

            if not cxs.isrunning():
                import webbrowser
                import threading

                def callback(event):
                    webbrowser.open_new(OS_LINK)

                def showlink():
                    root = Tk()
                    root.lift()
                    root.resizable(width=False, height=False)
                    root.title(_('Searching for subtitles on opensubtitles.org'))
                    root.attributes("-topmost", 1)
                    oslogo = PhotoImage(file=OS_LOGO)
                    link = Label(root, image=oslogo, cursor="hand2")
                    link.pack()
                    link.bind("<Button-1>", callback)
                    root.mainloop()

                class GuiThread(threading.Thread):
                    def __init__(self):
                        threading.Thread.__init__(self)

                    def run(self):
                        showlink()

                guithread = GuiThread()
                guithread.start()

            config = Conf(CFG_FILE, CFG_DEFAULT)
            try:
                movie = Movie(sys.argv[1])
            except Exception:
                sys.exit(1)
            moviedetails = {"moviehash": movie.hash, "moviesize": movie.size, "sublanguageid": config["DEFAULT"]["language"]}
            query = [moviedetails, {"limit": 1}]
            key = config["DEFAULT"]["key"]
            address = config["DEFAULT"]["address"]
            try:
                with OsSession(address, key) as subserver:
                    subs = subserver.SearchSubtitles(subserver.token, query)["data"][0]
                    if subs == None: raise SubExceptions("Empty_List", _("No subtitles found"))
            except SubExceptions as e:
                tkinter.messagebox.showerror(e.expression, e.message)
                sys.exit(1)
            try:
                zipsub = ZipFile(urlretrieve(subs["ZipDownloadLink"])[0])
                fname = zipsub.extract(subs["SubFileName"], os.path.dirname(movie.filename))
                os.rename(fname, os.path.splitext(movie.filename)[0] + '_' + subs["SubLanguageID"] + ".srt")
            except FileExistsError:
                tkinter.messagebox.showerror(title="File Exist", message=_("Subtitles file already exist"))
                pass







