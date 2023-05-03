import yaml,os


class config:
    def __init__(self, path):
        self.path = path
        self.data = self.loadData()

    def loadData(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w', encoding='utf-8'):
                print('')
        with open(self.path, encoding='utf-8') as c:
            return yaml.load(c, Loader=yaml.FullLoader)

    def saveData(self):
        with open(self.path, "w", encoding='utf-8') as f:
            yaml.dump(self.data, f)
