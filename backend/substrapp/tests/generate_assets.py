import os
import json
import substra


dir_path = os.path.dirname(__file__)
assets_path = os.path.join(dir_path, 'assets.py')


def main():

    client = substra.Client()
    client.add_profile('owkin', 'substra', 'p@$swr0d44', 'http://substra-backend.owkin.xyz:8000', '0.0')
    client.login()

    client.set_profile('owkin')

    assets = {}
    assets['objective'] = json.dumps(client.list_objective(), indent=4)
    assets['datamanager'] = json.dumps(client.list_dataset(), indent=4)
    assets['algo'] = json.dumps(client.list_algo(), indent=4)
    assets['traintuple'] = json.dumps(client.list_traintuple(), indent=4)
    assets['testtuple'] = json.dumps(client.list_testtuple(), indent=4)

    assets['model'] = json.dumps([res for res in client.client.list('model')
                                  if ('traintuple' in res and 'testtuple' in res)], indent=4)

    with open(assets_path, 'w') as f:
        f.write('"""\nWARNING\n=======\n\nDO NOT MANUALLY EDIT THIS FILE!\n\n'
                'It is generated using substrapp/tests/generate_assets.py\n\n'
                'In order to update this file:\n'
                '1. start a clean instance of substra\n'
                '2. run populate.py\n'
                '3. run substrapp/tests/generate_assets.py\n"""\n\n')
        for k, v in assets.items():
            v = v.replace('substra-backend.owkin.xyz:8000', 'testserver')
            v = v.replace('substra-backend.chunantes.xyz:8001', 'testserver')
            v = v.replace('true', 'True')
            v = v.replace('false', 'False')
            v = v.replace('null', 'None')
            f.write(f'{k} = {v}')
            f.write('\n\n')


if __name__ == '__main__':
    main()
