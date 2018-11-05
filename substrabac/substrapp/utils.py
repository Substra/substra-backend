import hashlib
import json
import os
import subprocess
import threading

from rest_framework import status

from substrabac.settings.common import PROJECT_ROOT, LEDGER_CONF


#######
# /!\ #
#######

# careful, passing invoke parameters to queryLedger will NOT fail


def queryLedger(options):
    org = options['org']
    peer = options['peer']
    args = options['args']

    org_name = org['name']

    # update config path for using right core.yaml in /substra/conf/<org>/<peer>-host
    # careful, directory is <peer>-host not <peer>
    cfg_path = '/substra/conf/' + org_name + '/' + peer['name'] + '-host'
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH', cfg_path)

    channel_name = LEDGER_CONF['misc']['channel_name']
    chaincode_name = LEDGER_CONF['misc']['chaincode_name']

    print('Querying chaincode in the channel \'%(channel_name)s\' on the peer \'%(peer_host)s\' ...' % {
        'channel_name': channel_name,
        'peer_host': peer['host']
    }, flush=True)

    output = subprocess.run([os.path.join(PROJECT_ROOT, '../bin/peer'),
                             '--logging-level=debug',
                             'chaincode', 'query',
                             '-x',
                             '-C', channel_name,
                             '-n', chaincode_name,
                             '-c', args],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    st = status.HTTP_200_OK
    data = output.stdout.decode('utf-8')
    if data:
        # json transformation if needed
        try:
            data = json.loads(bytes.fromhex(data.rstrip()).decode('utf-8'))
        except:
            # TODO : Handle error
            pass

        msg = 'Query of channel \'%(channel_name)s\' on peer \'%(peer_host)s\' was successful\n' % {
            'channel_name': channel_name,
            'peer_host': peer['host']
        }
        print(msg, flush=True)
    else:
        try:
            msg = output.stderr.decode('utf-8').split('Error')[2].split('\n')[0]
            data = {'message': msg}
        except:
            msg = output.stderr.decode('utf-8')
            data = {'message': msg}
        finally:
            st = status.HTTP_400_BAD_REQUEST
            if 'access denied' in msg:
                st = status.HTTP_403_FORBIDDEN

    return data, st


def invokeLedger(options, sync=False):
    org = options['org']
    peer = options['peer']
    args = options['args']

    org_name = org['name']

    orderer = LEDGER_CONF['orderers']['orderer']
    orderer_ca_file = '/substra/data/orgs/orderer/ca-cert.pem'
    orderer_key_file = '/substra/data/orgs/' + org_name + '/tls/' + peer['name'] + '/cli-client.key'
    orderer_cert_file = '/substra/data/orgs/' + org_name + '/tls/' + peer['name'] + '/cli-client.crt'

    # update config path for using right core.yaml in /substra/conf/<org>/<peer>-host
    # careful, directory is <peer>-host not <peer>
    cfg_path = '/substra/conf/' + org_name + '/' + peer['name'] + '-host'
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH', cfg_path)

    channel_name = LEDGER_CONF['misc']['channel_name']
    chaincode_name = LEDGER_CONF['misc']['chaincode_name']

    print('Sending invoke transaction to %(PEER_HOST)s ...' % {'PEER_HOST': peer['host']}, flush=True)

    cmd = [os.path.join(PROJECT_ROOT, '../bin/peer'),
           '--logging-level=debug',
           'chaincode', 'invoke',
           '-C', channel_name,
           '-n', chaincode_name,
           '-c', args,
           '-o', '%(host)s:%(port)s' % {'host': orderer['host'], 'port': orderer['port']},
           '--cafile', orderer_ca_file,
           '--tls',
           '--clientauth',
           '--keyfile', orderer_key_file,
           '--certfile', orderer_cert_file]

    if sync:
        cmd.append('--waitForEvent')

    output = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    if sync:
        st = status.HTTP_200_OK
    else:
        st = status.HTTP_201_CREATED

    data = output.stdout.decode('utf-8')

    if not data:
        msg = output.stderr.decode('utf-8')
        data = {'message': msg}

        if 'Error' in msg or 'ERRO' in msg:
            st = status.HTTP_400_BAD_REQUEST
        elif 'access denied' in msg or 'authentication handshake failed' in msg:
            st = status.HTTP_403_FORBIDDEN
        elif 'Chaincode invoke successful' in msg:
            st = status.HTTP_201_CREATED
            try:
                msg = msg.split('result: status:')[1].split('\n')[0].split('payload:')[1].strip().strip('"')
            except:
                pass
            finally:
                data = {'pkhash': msg}

    return data, st


def compute_hash(bytes):
    sha256_hash = hashlib.sha256()

    if isinstance(bytes, str):
        bytes = bytes.encode()

    sha256_hash.update(bytes)

    return sha256_hash.hexdigest()


def get_cpu_sets(cpu_count, concurrency):
    cpu_step = max(1, cpu_count // concurrency)
    cpu_sets = []

    for cpu_start in range(0, cpu_count, cpu_step):
        cpu_set = '%s-%s' % (cpu_start, cpu_start + cpu_step - 1)
        cpu_sets.append(cpu_set)

    return cpu_sets


def get_gpu_sets(gpu_list, concurrency):
    gpu_count = len(gpu_list)
    gpu_step = max(1, gpu_count // concurrency)
    gpu_sets = []

    for igpu_start in range(0, gpu_count, gpu_step):
        gpu_sets.append(','.join(gpu_list[igpu_start: igpu_start + gpu_step]))

    return gpu_sets


def update_statistics(job_statistics, stats, gpu_stats):

    # CPU

    if stats is not None:

        if 'cpu_stats' in stats and stats['cpu_stats']['cpu_usage'].get('total_usage', None):
            # Compute CPU usage in %
            delta_total_usage = (stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage'])
            delta_system_usage = (stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage'])
            total_usage = (delta_total_usage / delta_system_usage) * stats['cpu_stats']['online_cpus'] * 100.0

            job_statistics['cpu']['current'].append(total_usage)
            job_statistics['cpu']['max'] = max(job_statistics['cpu']['max'],
                                               max(job_statistics['cpu']['current']))

        # MEMORY in GB
        if 'memory_stats' in stats:
            current_usage = stats['memory_stats'].get('usage', None)
            max_usage = stats['memory_stats'].get('max_usage', None)

            if current_usage:
                job_statistics['memory']['current'].append(current_usage / 1024**3)
            if max_usage:
                job_statistics['memory']['max'] = max(job_statistics['memory']['max'],
                                                      max_usage / 1024**3,
                                                      max(job_statistics['memory']['current']))

        # Network in kB
        if 'networks' in stats:
            job_statistics['netio']['rx'] = stats['networks']['eth0'].get('rx_bytes', 0)
            job_statistics['netio']['tx'] = stats['networks']['eth0'].get('tx_bytes', 0)

    # GPU

    if gpu_stats is not None:
        total_usage = sum([100 * gpu.load for gpu in gpu_stats])
        job_statistics['gpu']['current'].append(total_usage)
        job_statistics['gpu']['max'] = max(job_statistics['gpu']['max'],
                                           max(job_statistics['gpu']['current']))

        total_usage = sum([gpu.memoryUsed for gpu in gpu_stats]) / 1024
        job_statistics['gpu_memory']['current'].append(total_usage)
        job_statistics['gpu_memory']['max'] = max(job_statistics['gpu_memory']['max'],
                                                  max(job_statistics['gpu_memory']['current']))

    # IO DISK
    # "blkio_stats": {
    #   "io_service_bytes_recursive": [],
    #   "io_serviced_recursive": [],
    #   "io_queue_recursive": [],
    #   "io_service_time_recursive": [],
    #   "io_wait_time_recursive": [],
    #   "io_merged_recursive": [],
    #   "io_time_recursive": [],
    #   "sectors_recursive": []
    # }

    # LOGGING
    # printable_stats = 'CPU - now : %d %% / max : %d %% | MEM - now : %.2f GB / max : %.2f GB' % \
    #     (job_statistics['cpu']['current'][-1],
    #      job_statistics['cpu']['max'],
    #      job_statistics['memory']['current'][-1],
    #      job_statistics['memory']['max'])

    # logging.info('[JOB] Monitoring : %s' % (printable_stats, ))


class ExceptionThread(threading.Thread):

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self._exception = e
            raise e
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs
