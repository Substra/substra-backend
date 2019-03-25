import opener


def open_data_samples(data_folder='./data'):
    """Open data sample with the opener"""
    opener.get_X(data_folder)
    opener.get_y(data_folder)


if __name__ == "__main__":
    open_data_samples()
