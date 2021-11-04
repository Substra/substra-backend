import os
import json
import substra
from datetime import datetime
import textwrap

URL = 'http://substra-backend.node-1.com'
USERNAME = 'node-1'
PASSWORD = 'p@sswr0d44'

dir_path = os.path.dirname(__file__)
assets_path = os.path.join(dir_path, 'assets.py')


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def main():

    client = substra.Client(url=URL, insecure=False)
    client.login(USERNAME, PASSWORD)

    assets = {}

    assets['metrics'] = client.list_metric()
    assets['data_managers'] = client.list_dataset()
    assets['algos'] = client.list_algo()
    assets['train_tasks'] = client.list_traintuple()

    # Add tag for unit tests
    tt = client.list_testtuple()
    tt[0].tag = 'bar'
    tt[1].tag = 'foo'
    assets['test_tasks'] = tt

    assets['compute_plans'] = client.list_compute_plan()

    # Add tag for unit tests
    ct = client.list_composite_traintuple()
    ct[0].tag = 'substra'
    assets['composite_tasks'] = ct

    assets['models'] = client._backend.list(substra.sdk.schemas.Type.Model)

    with open(assets_path, 'w') as f:
        f.write('"""\nWARNING\n=======\n\nDO NOT MANUALLY EDIT THIS FILE!\n\n'
                'It is generated using substrapp/tests/generate_assets.py\n\n'
                'In order to update this file:\n'
                '1. start a clean instance of substra\n'
                '2. run computation on it (with e2e tests for instance)\n'
                '3. run substrapp/tests/generate_assets.py\n"""\n\n')
        for k, v in assets.items():
            v = json.dumps([asset.dict() for asset in v], cls=DateEncoder, indent=4)
            v = v.replace(URL, 'http://testserver')
            v = v.replace('true', 'True')
            v = v.replace('false', 'False')
            v = v.replace('null', 'None')
            v = textwrap.indent(v, 4 * ' ').lstrip(" ")
            f.write(f'def get_{k}():\n')
            f.write(f'    return {v}\n')
            f.write('\n\n')
            f.write(f'def get_{k[:-1]}():\n')
            f.write(f'    return get_{k}()[0]\n')
            f.write('\n\n')


if __name__ == '__main__':
    main()
