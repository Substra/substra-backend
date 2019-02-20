import opener


def open_data(data_folder='./data'):
    """Open data with the opener"""
    opener.get_X(data_folder)
    opener.get_y(data_folder)


if __name__ == "__main__":
    open_data()
