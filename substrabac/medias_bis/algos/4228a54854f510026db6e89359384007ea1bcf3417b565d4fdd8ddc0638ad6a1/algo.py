"""Submission example with sklearn 2"""
import sys
import logging
import numpy as np
from sklearn.linear_model import SGDClassifier

from substratools import SubstraModel
import opener

# For now, logging will not be reported in Substra for security reasons
logging.basicConfig(filename='model/log_model.log', level=logging.DEBUG)


class Model(SubstraModel):
    """Class for submitted algo/model derives from the SubstraModel class
    defined in substratools"""
    def __init__(self, data_folder="./data", pred_folder="./pred", model_file="./model/model"):
        super().__init__(data_folder=data_folder, pred_folder=pred_folder, model_file=model_file)
        self.clf = SGDClassifier(warm_start=True, loss='log', random_state=42)
        # check if existing estimated params and update model if it is the case
        try:
            self.load_json_sklearn(self.clf)
            logging.info("Model successfully loaded")
            print("Model successfully loaded")
        except FileNotFoundError:
            logging.info("No model found, use algo")

    def train(self):
        # extract data
        logging.info("Getting data")
        X_train = opener.get_X(self.data_folder)
        y_train = opener.get_y(self.data_folder)
        # standardize data
        X_train = X_train.reshape(X_train.shape[0], -1)
        X_train = (X_train - np.mean(X_train, axis=0)) / np.std(X_train, axis=0)
        # fit model on data
        logging.info("Fitting model")
        self.clf.fit(X_train, y_train.argmax(axis=1))
        # save trained model -- DO NOT FORGET THIS STEP
        logging.info("Saving fitted model")
        self.save_json_sklearn(self.clf)
        # save prediction on train data in pred folder
        y_pred = self.clf.predict_proba(X_train)
        opener.save_pred(y_pred, self.pred_folder)

    def pred(self):
        # extract data and standardize
        X_test = opener.get_X(self.data_folder)
        X_test = X_test.reshape(X_test.shape[0], -1)
        X_test = (X_test - np.mean(X_test, axis=0)) / np.std(X_test, axis=0)
        # compute prediction on data
        y_pred = self.clf.predict_proba(X_test)
        # save prediction on test data in pred folder
        opener.save_pred(y_pred, self.pred_folder)


if __name__ == "__main__":
    task = sys.argv[1]

    if task == "train":
        logging.info("Starting train...")
        model = Model()
        model.train()
    elif task == "predict":
        logging.info("Starting predict...")
        model = Model()
        model.pred()
    else:
        raise ValueError("task not implemented, should be either train or predict")