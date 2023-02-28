import json
import logging


def readJson(fileName):
    try:
        with open(fileName, 'r', encoding='utf8') as file:
            try:
                fileData = json.load(file)
                return True, fileData
            except:
                logging.info(f'{fileName} is blank!')
                return False, {}
    except EnvironmentError:
        logging.info(f'Not found {fileName}')
        return False, {}
