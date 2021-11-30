import substratools as tools
from sklearn.metrics import recall_score


class Metrics(tools.Metrics):
    def score(self, y_true, y_pred):
        return recall_score(y_true.argmax(axis=1), y_pred.argmax(axis=1), average="macro")


if __name__ == "__main__":
    tools.metrics.execute(Metrics())
