class DataCollector:
    def __init__(self, model):
        self.model = model
        self.data = {}
        self.record = {}
    
    def register(self, attr, record=True):
        if attr not in self.data.keys():
            self.data[attr] = []
            self.record[attr] = record
        

    def collect_data(self):
        if hasattr(self.model, "collect_data"):
            self.model.collect_data()

        for attr in self.data.keys():
            if hasattr(self.model, attr):
                data = getattr(self.model, attr)
            else:
                data = None
            if self.record[attr]:
                self.data[attr].append(data)
            else:
                self.data[attr] = data
            