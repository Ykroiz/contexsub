__author__ = 'davbr'

import os
import configparser
from tkinter import *

class Conf(configparser.ConfigParser):
    def __init__(self, configfile, cfgdefaults):
        super(Conf, self).__init__()
        self.configfile = configfile
        if not os.path.exists(configfile):
            for key, value in cfgdefaults.items():
                self[key] = value
            with open(configfile, 'w') as cfgfile:
                self.write(cfgfile)
        else:
            self.read(configfile)

    def guiconf(self):
        guifields={"DEFAULT": {}}
        root = Tk()

        def callback():
            nonlocal self
            for section in guifields.keys():
                for key in guifields[section]:
                    self[section][key] = guifields[section][key].get()
            with open(self.configfile, 'w') as cfgfile:
                self.write(cfgfile)

        for key in self["DEFAULT"].keys():
            frame = Frame(root)
            frame.pack(side=TOP)
            Label(frame, text=key).pack(side=LEFT)
            guifields["DEFAULT"][key] = Entry(frame)
            guifields["DEFAULT"][key].insert(0, self["DEFAULT"][key])
            guifields["DEFAULT"][key].pack(side=LEFT)

        for section in self.sections():
            secframe = Frame(root)
            secframe.pack(side=TOP)
            Label(secframe, text=section).pack(side=LEFT)
            for key in self[section]:
                frame = Frame(secframe)
                frame.pack(side=TOP)
                Label(frame, text=key).pack(side=LEFT)
                guifields[section][key] = Entry(frame)
                guifields[section][key].insert(0, self[section][key])
                guifields[section][key].pack(side=LEFT)

        Button(root, text="Save", command=callback).pack(side=TOP)
        root.mainloop()
