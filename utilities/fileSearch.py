import os

class FileSearch:

    @staticmethod
    def collectFilesEndsWithNameRecursively(name, folderPath):
        fileList = []

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if name is None or file.endswith(name):
                    fileList.append(os.path.join(root, file))

        return fileList

    @staticmethod
    def collectFilesEndsWithName(name, folderPath):
        fileList = []

        for file in os.listdir(folderPath):
            if name is None or file.endswith(name):
                fileList.append(os.path.join(folderPath, file))

        return fileList
