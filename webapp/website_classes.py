class Message:

    def __init__(self, type: str, role: str, content: str):
        self.type = type
        self.role = role
        self.content = content
        self.labels_gen = None
        self.labels_asoc = None
        self.labels_risk = None
        self.labels_dims = None
        self.color = None
        self.annotation = None

    def add_color(self):
        if self.type == "input":
            if self.labels_gen: self.color = "#bae1ff" # light blue
            elif self.labels_asoc: self.color = "#ffdfba" # light orange
            elif self.labels_risk: self.color = "#f1cbff" # light violet
        elif self.type == "output":
            if self.labels_dims: self.color = "#ffb3ba" # light red

    def add_annotation(self):
        all_labels = []
        for category in [self.labels_gen, self.labels_asoc, self.labels_risk, self.labels_dims]:
            if category is not None: 
                all_labels.extend(category)
        all_labels = list(dict.fromkeys(all_labels))
        if all_labels: self.annotation = ", ".join(all_labels)
        