import logging
import logging.config
import yaml
import coloredlogs
import os

#class infoFilter(logging.Filter):
#    def filter(self, rec):
#        return rec.levelno == logging.INFO

def setupLogging():
    default_level = logging.INFO
    if os.path.exists('./config/logging.yaml'):
        with open('./config/logging.yaml', 'rt') as file:
            try:
                config = yaml.safe_load(file.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)
        print('Failed to load configuration file. Using default configs')
                
