from ConfigParser import RawConfigParser, SafeConfigParser, NoOptionError

class EqualsSpaceRemover:
    output_file = None
    def __init__( self, new_output_file ):
        self.output_file = new_output_file

    def write( self, what ):
        self.output_file.write( what.replace( " = ", "=" ) )

class configSystem:
    __config = None
    def __init__(self, configFile):
        self.__config = SafeConfigParser(allow_no_value=True)
        self.__config.read(configFile)

    def getConfigValue(self, section, parameter):
        try:
            return self.__config.get(section, parameter)
        except NoOptionError:
            return None
        except NoSectionError:
            return None

    def setConfigValue(self, section, parameter, value):
        print 'setting: section: %s parameter: %s value: %s' % (section, parameter, value)
        return self.__config.set(section, parameter, value)

    def writeConfig(self, configFile):
        e = open(configFile, 'wb')
        rtn = self.__config.write(EqualsSpaceRemover(e))
        e.close()
        return rtn

