__author__ = 'davbr'
import os
from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS
from tkinter import *
import tkinter.messagebox
import gettext
from confgui import Conf
from ossession import *
import struct


try:
    APP_PATH = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
except NameError:
    import sys
    APP_PATH = os.path.normpath(os.path.dirname(os.path.realpath(sys.argv[0])))

OS_LOGO = APP_PATH + "\\oslogo.gif"
CFG_FILE = os.path.join(os.path.join(os.environ['USERPROFILE'], "Appdata\\roaming"), "contexsub") + "\\contexsub.cfg"
LOCALE_PATH = APP_PATH + "\\locale\\"
OS_LINK = 'http://www.opensubtitles.org'
CFG_DEFAULT = {"USER": {"language": "eng",
                           "username": "",
                           "password": ""},
               "OS_CFG": {"key": "contexsub",
                          "address": "https://api.opensubtitles.org/xml-rpc"}
               }

gettext.bindtextdomain('contexsub', LOCALE_PATH)
gettext.textdomain('contexsub')
_ = gettext.gettext



class Movie:
    """
    Details of video to fetch subtitles for.
    :Movie.size: file bytesize
    :Movie.hash: file hash used by opensubtitles.org
    """
    def __init__(self, filename):
        """
        :param filename: Video filename
        :return:
        """
        self.filename = filename
        self.size = os.path.getsize(filename)
        self.hash = self._movieHash()

    def _movieHash(self):
        longlongformat = '<q'
        bytesize = struct.calcsize(longlongformat)
        try:
            with open(self.filename, 'rb') as f:
                hash = self.size

                if self.size < 65536 * 2:
                    raise Exception("SizeError")

                for x in range(65536//bytesize):
                    buffer = f.read(bytesize)
                    (l_value,)= struct.unpack(longlongformat, buffer)
                    hash += l_value
                    hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number

                f.seek(max(0,self.size-65536),0)
                for x in range(65536//bytesize):
                    buffer = f.read(bytesize)
                    (l_value,)= struct.unpack(longlongformat, buffer)
                    hash += l_value
                    hash = hash & 0xFFFFFFFFFFFFFFFF

                returnedhash =  "%016x" % hash
                return returnedhash
        except(IOError):
            raise
        except(Exception("SizeError")):
            raise



class SingleInstance:
    """
    Used to check if multiple instances of the program are running
    """

    def __init__(self):
        """
        Using win32py, creates a mutex distinctive to this program
        :return:
        """
        self.mutexui = 'cxsmutex_{CA99EC98-5C30-4CB3-8F3C-818948AE81B9}'
        self.mutex = CreateMutex(None, False, self.mutexui)
        self.lasterror = GetLastError()

    def isrunning(self):
        """

        :return: True if another instance of the program is running, False otherwise
        """
        return self.lasterror == ERROR_ALREADY_EXISTS

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)



def displayoslink():
    """
    Displays a box with OpenSubtitles logo, clicking on it will open browser at www.opensubtitles.org
    :return:
    """
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
        """
        Open the box in a new thread, while fetching subtitles in background
    :return:
    """
        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            showlink()

    guithread = GuiThread()
    guithread.start()


if __name__ == "__main__":
    if len(sys.argv) >= 2:  # Argument is a filename of the video file, or none to open configuration gui
            cxs = SingleInstance()
            # We only display the link once.
            if not cxs.isrunning():
                displayoslink()

            config = Conf(CFG_FILE, CFG_DEFAULT)
            try:
                movie = Movie(sys.argv[1])
            except Exception:
                sys.exit(1)
            # Search for subtitles by hash
            moviedetails = {
                "moviehash": movie.hash,
                "moviesize": movie.size,
                "sublanguageid": config["USER"]["language"]
            }
            query = [moviedetails, {"limit": 1}]
            key = config["OS_CFG"]["key"]
            address = config["OS_CFG"]["address"]
            try:
                with OsSession(address, key) as subserver:
                    # SearchSubtitles is implemented by server XML-RPC
                    subs = subserver.SearchSubtitles(query)["data"][0]
                    if subs == None: raise SubExceptions("Empty_List", _("No subtitles found"))
                    # many players automatically use sub file with filename similiar to the video's
                    if os.path.exists(os.path.splitext(movie.filename)[0] + '_' + subs["SubLanguageID"] + ".srt"):
                        raise FileExistsError
                    else:
                        with open(os.path.splitext(movie.filename)[0] + '_' + subs["SubLanguageID"] + ".srt", "wb") as f:
                            f.write(subserver.GetSubtitles(subs))
            except SubExceptions as e:
                tkinter.messagebox.showerror(e.expression, e.message)
                sys.exit(1)
            except FileExistsError:
                tkinter.messagebox.showerror(title="File Exist", message=_("Subtitles file already exist"))
                pass
    else:
        config = Conf(CFG_FILE, CFG_DEFAULT)
        config.guiconf(hide=("OS_CFG",))
