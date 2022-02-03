import os

class DictionaryMap(object):

    @staticmethod
    def getByPath(dict, path):
        subKeys = path.split(".")
        curDictValue = dict

        for subKey in subKeys:
            if subKey in curDictValue:
                curDictValue = curDictValue[subKey]
            else:
                return None

        return curDictValue
        