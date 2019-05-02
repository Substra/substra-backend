import substratools as tools


if __name__ == "__main__":
    opener = tools.opener.load_from_module()
    opener.get_X()
    opener.get_y()
