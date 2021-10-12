import os
import json
import substra
from datetime import datetime

URL = 'http://substra-backend.node-1.com'
USERNAME = 'node-1'
PASSWORD = 'p@$swr0d44'

dir_path = os.path.dirname(__file__)
assets_path = os.path.join(dir_path, 'assets.py')


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def json_dumps(assets):
    return json.dumps(
        [a.dict() for a in assets],
        cls=DateEncoder,
        indent=4
    )


def main():

    client = substra.Client(url=URL, insecure=False)
    client.login(USERNAME, PASSWORD)

    assets = {}

    assets['metric'] = json_dumps(client.list_metric())
    assets['datamanager'] = json_dumps(client.list_dataset())
    assets['algo'] = json_dumps(client.list_algo())
    assets['traintuple'] = json_dumps(client.list_traintuple())

    # Add tag for unit tests
    tt = client.list_testtuple()
    tt[0].tag = 'bar'
    tt[1].tag = 'foo'
    assets['testtuple'] = json_dumps(tt)

    assets['computeplan'] = json_dumps(client.list_compute_plan())

    # Add tag for unit tests
    ct = client.list_composite_traintuple()
    ct[0].tag = 'substra'
    assets['compositetraintuple'] = json_dumps(ct)

    assets['model'] = json_dumps(client._backend.list(substra.sdk.schemas.Type.Model))

    with open(assets_path, 'w') as f:
        f.write('"""\nWARNING\n=======\n\nDO NOT MANUALLY EDIT THIS FILE!\n\n'
                'It is generated using substrapp/tests/generate_assets.py\n\n'
                'In order to update this file:\n'
                '1. start a clean instance of substra\n'
                '2. run computation on it (with e2e tests for instance)\n'
                '3. run substrapp/tests/generate_assets.py\n"""\n\n')
        for k, v in assets.items():
            v = v.replace(URL, 'http://testserver')
            v = v.replace('true', 'True')
            v = v.replace('false', 'False')
            v = v.replace('null', 'None')
            f.write(f'{k} = {v}')
            f.write('\n\n')


if __name__ == '__main__':
    main()
