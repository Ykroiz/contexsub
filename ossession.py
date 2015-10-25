__author__ = 'davbr'

from xmlrpc.client import ServerProxy, Error



class SubExceptions(Exception):
    """
    Deal with exceptions emerging from login attempts and empty search results
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message



class OsSession(ServerProxy):
    """
    XML-RPC session with opensubtitles
    """
    def __init__(self, address, key, username="", password="", lang="en"):
        """
        :param address: OpenSubtitles server address
        :param key: OpenSubtitles user agent key
        :param username: Optional client username for opensubtitles.org
        :param password: Optional password for aforementioned username
        :param lang: THIS IS NOT THE LANGUAGE FOR THE SUBTITLES. this is language for th opensubtitles.org api
            Usually there is no reason to change this
        :return:
        """
        super(OsSession, self).__init__(address)
        login = self.LogIn(username, password, lang, key)  # LogIn is implemented by server XML-RPC
        if login["status"] != "200 OK":
            raise SubExceptions(login["status"], _("Login to OpenSubtitles failed"))
        else:
            self._token = login["token"]  # Token used for communicating with server
            self._SearchSubtitles = self.SearchSubtitles
            self.SearchSubtitles = self.makeSearchSubtitles(self._token)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.LogOut(self._token)

    def makeSearchSubtitles(self, token):
        def SearchSubtitles(*args):
            return self._SearchSubtitles(token, *args)
        return SearchSubtitles

    def GetSubtitles(self, subs):
        import base64
        import gzip
        return gzip.decompress(
            base64.b64decode(
                self.DownloadSubtitles(self._token, (subs["IDSubtitleFile"],))["data"][0]["data"])
            )
