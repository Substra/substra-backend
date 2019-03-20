import os
import subprocess

from hfc.fabric import Client

from substrabac.settings.common import PROJECT_ROOT

dir_path = os.path.dirname(os.path.realpath(__file__))

cli = Client(net_profile=os.path.join(dir_path, '../network.json'))
admin_owkin = cli.get_user('owkin', 'admin')

cli.new_channel('mychannel')

from hfc.fabric_ca.caservice import ca_service

cacli = ca_service(target="https://rca-owkin:7054",
                   ca_certs_path='/substra/data/orgs/owkin/ca-cert.pem',
                   ca_name='rca-owkin')

print('Will try to enroll admin')
try:
    admin = cacli.enroll('admin-owkin', 'admin-owkinpw')
except ValueError as e:
    print(e)
except Exception as e:
    print(e)
else:
    print('Admin enrolled')

    os.environ['FABRIC_CFG_PATH'] = '/substra/conf/owkin/peer1'
    os.environ['CORE_PEER_MSPCONFIGPATH'] = '/substra/data/orgs/owkin/user/msp'

    output = subprocess.run([os.path.join(PROJECT_ROOT, '../bin/peer'),
                             '--logging-level', 'DEBUG',
                             'chaincode', 'query',
                             '-C', 'mychannel',
                             '-n', 'mycc',
                             #'--tls',
                             #'--clientauth',
                             '-c', '{"Args":["queryDatasets"]}'
                             ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    data = output.stdout.decode('utf-8')
    if data:
        print(data)
    else:
        try:
            msg = output.stderr.decode('utf-8').split('Error')[2].split('\n')[0]
            data = {'message': msg}
        except:
            msg = output.stderr.decode('utf-8')
            data = {'message': msg}
        finally:
            print(data)

    response = cli.chaincode_query(
        requestor=admin_owkin,
        channel_name='mychannel',
        peer_names=['peer1-owkin'],
        args=[],
        cc_name='mycc',
        cc_version='1.0',
        fcn='queryDatasets'
    )
    print(response)

    response = cli.query_installed_chaincodes(
        requestor=admin_owkin,
        peer_names=['peer1-owkin']
    )
    print(response)

    response = cli.query_channels(
        requestor=admin_owkin,
        peer_names=['peer1-owkin']
    )
    print(response)

    response = cli.query_info(
        requestor=admin_owkin,
        channel_name='mychannel',
        peer_names=['peer1-owkin']
    )
    print(response)

    dir_path = os.path.dirname(os.path.realpath(__file__))

    response = cli.chaincode_invoke(
        requestor=admin_owkin,
        channel_name='mychannel',
        peer_names=['peer1-owkin'],
        args=['ISIC 2018',
              '6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181',
              'http://chunantes.substrabac:8001/media/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/opener.py',
              'Images',
              '6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181',
              'http://chunantes.substrabac:8001/media/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/description.md',
              '',
              'all'
              ],
        cc_name='mycc',
        cc_version='1.0',
        fcn='registerDataset',
        wait_for_event=True,
        wait_for_event_timeout=5
    )
    print(response)
