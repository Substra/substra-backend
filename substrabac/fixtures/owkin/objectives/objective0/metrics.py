from sklearn.metrics import recall_score

from substratools import Metrics as MetricsABC


class Metrics(MetricsABC):
    def score(self, y_true, y_pred):
        return recall_score(y_true.argmax(axis=1), y_pred.argmax(axis=1), average='macro')
