from ConfigParser import RawConfigParser

class configSystem:
    __config = None
    def __init__(self, configFile):
        self.__config = RawConfigParser()
        self.__config.read(configFile)

    def getConfigValue(self, section, parameter):
        return self.__config.get(section, parameter)