"""Opener of the simplified ISIC 2018 dataset"""

import csv
import os

import numpy as np
import substratools as tools
from PIL import Image

PREFIX_X = "IMG_"
SUFFIX_X = ".jpg"
PREFIX_Y = "LABEL_"
SUFFIX_Y = ".csv"
PRED_FILE = "pred.csv"

# Data Description
SIZE_X = 450
SIZE_Y = 600
SIZE_Z = 3
CLASSES = 7

n_sample = 10


def _check_existing_files(files):
    """check if files from a list of files are located in folder"""
    for f in files:
        if not os.path.isfile(f):
            raise FileNotFoundError("non existing file %s" % (f))


def _get_paths(folders):
    """return list of features and label files given a folder location (with
    the same order)"""
    # get list of features files and create associated list of label files
    X_files = [os.path.join(folder, f) for folder in folders for f in os.listdir(os.path.join(folder)) if ".jpg" in f]
    y_files = [f.replace(PREFIX_X, PREFIX_Y).replace(SUFFIX_X, SUFFIX_Y) for f in X_files]

    # check label files exist
    try:
        _check_existing_files(y_files)
    except FileNotFoundError as e:
        print(str(e))
        y_files = None
    return X_files, y_files


class MyOpener(tools.Opener):
    def get_X(self, folders):
        print("Finding features files...")
        X_paths, _ = _get_paths(folders)
        print("Loading features...")
        X = []
        for path in X_paths:
            image = Image.open(path)
            X.append(np.array(image))
        return np.array(X)

    def get_y(self, folders):
        print("Finding label files...")
        _, y_paths = _get_paths(folders)
        print("Loading labels...")
        y = []
        for path in y_paths:
            with open(path) as f:
                str_y = f.readline().split(",")
            y.append([float(yy) for yy in str_y])
        return np.array(y, dtype=np.float)

    def fake_X(self):
        """Make and return the ISIC like features data as np arrays."""
        return np.random.randint(low=0, high=256, size=(n_sample, SIZE_X, SIZE_Y, SIZE_Z)).astype("uint8")

    def fake_y(self):
        """Make and return the ISIC like labels as np arrays."""
        return np.eye(CLASSES)[np.arange(n_sample) % CLASSES].astype("uint8")

    def save_predictions(self, y_pred, path):
        """Save prediction in path

        :param y_pred: predicted target variable vector
        :type y_pred: numpy array
        :param folder: path to the folder in which to save the predicted target variable vector
        :type folder: string
        :return: None
        """
        with open(path, "w") as f:
            writer = csv.writer(f)
            writer.writerows(y_pred)

    def get_predictions(self, path):
        """Get predictions which were saved using the save_pred function

        :param folder: path to the folder where the previously predicted target variable vector has been saved
        :type folder:  string
        :return: predicted target variable vector
        :rtype: numpy array
        """
        with open(path, "r") as f:
            pred_iter = csv.reader(f)
            pred = [y for y in pred_iter]
        return np.array(pred, copy=False, dtype=np.float)
