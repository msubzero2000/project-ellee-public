import json

class JsonFile(object):
    @staticmethod
    def jsonFromFile(filePath):
        with open(filePath, "r") as handle:
            return json.loads(handle.read())

    @staticmethod
    def jsonToFile(filePath, jsonObj):
        try:
            with open(filePath, "w") as handle:
                handle.write(json.dumps(jsonObj, sort_keys=True, indent=4, separators=(',', ': ')))
        except Exception as e:
            print(e)