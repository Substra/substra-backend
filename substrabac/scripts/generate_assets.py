import os
import json
from substra_sdk_py import Client


dir_path = os.path.dirname(os.path.realpath(__file__))


def main():

    client = Client()
    client.create_config('owkin', 'http://owkin.substrabac:8000', '0.0')

    client.set_config('owkin')

    assets = {}
    assets['objective'] = json.dumps(client.list('objective'), indent=4)
    assets['datamanager'] = json.dumps(client.list('data_manager'), indent=4)
    assets['algo'] = json.dumps(client.list('algo'), indent=4)
    assets['traintuple'] = json.dumps(client.list('traintuple'), indent=4)
    assets['testtuple'] = json.dumps(client.list('testtuple'), indent=4)

    assets['model'] = json.dumps([res for res in client.list('model')
                                  if ('traintuple' in res and 'testtuple' in res)], indent=4)

    with open(os.path.join(dir_path, '../substrapp/tests/assets.py'), 'w') as f:
        for k, v in assets.items():
            v = v.replace('owkin.substrabac:8000', 'testserver')
            v = v.replace('chunantes.substrabac:8001', 'testserver')
            v = v.replace('true', 'True')
            v = v.replace('false', 'False')
            v = v.replace('null', 'None')
            f.write(f'{k} = {v}')
            f.write('\n\n')


if __name__ == '__main__':
    main()
