__author__ = 'davbr'

import os
import configparser
from tkinter import *

class Conf(configparser.ConfigParser):
    """
    Configparser, automatically creates config file if absent, and gui config editor
    """
    def __init__(self, configfile, cfgdefaults):
        """
        :param configfile: configuration file (string)
        :param cfgdefaults: default values. if configfile does not exist, it will be created with these defaults
        :return:
        """
        super(Conf, self).__init__()
        self.configfile = configfile
        if not os.path.exists(configfile):
            for key, value in cfgdefaults.items():
                self[key] = value
            if not os.path.exists(os.path.dirname(configfile)):
                os.makedirs(os.path.dirname(configfile))
            with open(configfile, 'w') as cfgfile:
                self.write(cfgfile)
        else:
            self.read(configfile)

    def guiconf(self, hide=("",)):
        """
        Simply iterate on all sections and fields, displaying a very basic gui to edit the configuration
        :param hide: list of sections to hide from gui
        :return:
        """
        guifields={}
        guifields.update({section: {} for section in self.sections()})
        guifields["DEFAULT"] = {key: {} for key in self["DEFAULT"].keys()}
        root = Tk()

        def callback():
            nonlocal self
            for section in guifields.keys():
                for key in guifields[section]:
                    self[section][key] = guifields[section][key].get()
            with open(self.configfile, 'w') as cfgfile:
                self.write(cfgfile)

        for section in ((set(self.sections()) | set(("DEFAULT",))) - set(hide)):
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
