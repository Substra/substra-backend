#!/usr/bin/env python

from secrets import choice


def gen_secret_key(r):
    return "".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for _ in range(r)])


def write_secret_key(path):
    secret_key = gen_secret_key(50)

    with open(path, "w") as f:
        f.write(secret_key)

    return secret_key


if __name__ == "__main__":
    print(gen_secret_key(50))
