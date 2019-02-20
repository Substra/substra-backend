import json
import metrics
import opener


def calc_perf(folder_pred="./pred"):
    """compute performances using the imported metrics.score function"""
    # get true and pred values
    y_true = opener.fake_y()
    y_pred = opener.fake_y()
    return {'all': metrics.score(y_true, y_pred)}


if __name__ == "__main__":
    perf = calc_perf()
    with open('./pred/perf.json', 'w') as outfile:
        json.dump(perf, outfile)
