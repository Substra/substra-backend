import glob
import socket

import time
from shutil import copytree, copy2
from subprocess import call, check_output, CalledProcessError, STDOUT

import os
import sys


def copy_last_file_ext(ext, src, dst):
    files = glob.iglob(os.path.join(src, ext))
    for file in files:
        if os.path.isfile(file):
            copy2(file, dst)


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# Wait for a process to begin to listen on a particular host and port
# Usage: waitPort <what> <timeoutInSecs> <errorLogFile> <host> <port>
def waitPort(what, secs, logFile, host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))

    if result != 0:
        sys.stdout.write('Waiting for %s ...\n' % what)
        sys.stdout.flush()
        starttime = int(time.time())

        while True:
            call(['sleep', '1'])
            result = sock.connect_ex((host, port))
            if result == 0:
                break

            if int(time.time()) - starttime > secs:
                sys.stdout.write('Failed waiting for %(what)s; see %(logFile)s\n' % {'what': what, 'logFile': logFile})
                sys.stdout.flush()
                break

            sys.stdout.write('.')
            sys.stdout.flush()


# Wait for one or more files to exist
def dowait(what, secs, logFile, files):
    logit = True
    starttime = int(time.time())

    for file in files:
        while not os.path.exists(file):
            if logit:
                sys.stdout.write('Waiting for %s ...\n' % what)
                sys.stdout.flush()
                logit = False
            call(['sleep', '1'])
            if int(time.time()) - starttime > secs:
                sys.stdout.write('Failed waiting for %(what)s; see %(logFile)s\n' % {'what': what, 'logFile': logFile})
                sys.stdout.flush()
                break
            sys.stdout.write('.')
            sys.stdout.flush()


def finishMSPSetup(org_msp_dir):
    src = org_msp_dir + '/cacerts/'
    dst = org_msp_dir + '/tlscacerts'
    if not os.path.exists(dst):
        copytree(src, dst)

        if os.path.exists(org_msp_dir + '/intermediatecerts'):
            # uncomment if using intermediate certs
            #copytree(org_msp_dir + '/intermediatecerts/', org_msp_dir + '/tlsintermediatecerts/')

            # no intermediate cert in this config, delete generated files for not seeing warning
            sys.stdout.write('Delete intermediate certs in ' + org_msp_dir + '/intermediatecerts/\n')
            sys.stdout.flush()
            for file in os.listdir(org_msp_dir + '/intermediatecerts/'):
                file_path = os.path.join(org_msp_dir + '/intermediatecerts/', file)
                if os.path.isfile(file_path):
                    os.remove(file_path)


def genClientTLSCert(host_name, cert_file, key_file, enrollment_url):
    call(['fabric-ca-client', 'enroll', '-d', '--enrollment.profile', 'tls', '-u', enrollment_url, '-M',
          '/tmp/tls', '--csr.hosts', host_name])

    create_directory('/data/tls')
    copy2('/tmp/tls/signcerts/cert.pem', cert_file)
    copy_last_file_ext('*_sk', '/tmp/tls/keystore/', key_file)
    call(['rm', '-rf', '/tmp/tls'])


# Copy the org's admin cert into some target MSP directory
# This is only required if ADMINCERTS is enabled.
def copyAdminCert(msp_config_path, org, setup_log_file, org_admin_cert):
    dstDir = msp_config_path + '/admincerts'
    create_directory(dstDir)
    dowait('%s administator to enroll' % org, 60, setup_log_file, [org_admin_cert])
    copy2(org_admin_cert, dstDir)


def switchToAdminIdentity(org):
    org_admin_home = org['admin_home']
    org_msp_dir = org['org_msp_dir']
    if not os.path.exists(org_admin_home + '/msp'):
        sys.stdout.write('enroll admin and copy in admincert\n')
        sys.stdout.flush()
        dowait('%(CA_NAME)s to start' % {'CA_NAME': org['ca']['name']},
               90,
               org['ca']['logfile'],
               [org['tls']['certfile']])

        sys.stdout.write('Enrolling admin \'%(ADMIN_NAME)s\' with %(CA_HOST)s...\n' % {
            'ADMIN_NAME': org['users']['admin']['name'],
            'CA_HOST': org['ca']['host']})
        sys.stdout.flush()

        data = {
            'CA_ADMIN_USER_PASS': '%(name)s:%(pass)s' % {
                'name': org['users']['admin']['name'],
                'pass': org['users']['admin']['pass'],
            },
            'CA_URL': '%(host)s:%(port)s' % {'host': org['ca']['host'], 'port': org['ca']['port']}
        }

        os.environ['FABRIC_CA_CLIENT_HOME'] = org_admin_home
        os.environ['FABRIC_CA_CLIENT_TLS_CERTFILES'] = org['tls']['certfile']

        # need to copy fabric-ca-client-config.yaml in admin
        #copy2(org_msp_dir + '/fabric-ca-client-config.yaml', org_admin_home + '/fabric-ca-client-config.yaml')

        call(['fabric-ca-client', 'enroll', '-d', '-u', 'https://%(CA_ADMIN_USER_PASS)s@%(CA_URL)s' % data])

        # no intermediate cert in this config, delete generated files for not seeing warning
        sys.stdout.write('Delete intermediate certs in ' + org_admin_home + '/msp' + '/intermediatecerts/\n')
        sys.stdout.flush()
        for file in os.listdir(org_admin_home + '/msp' + '/intermediatecerts/'):
            file_path = os.path.join(org_admin_home + '/msp' + '/intermediatecerts/', file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # If admincerts are required in the MSP, copy the cert there now and to my local MSP also
        create_directory(org_msp_dir + '/admincerts/')
        copy2(org_admin_home + '/msp/signcerts/cert.pem', org_msp_dir + '/admincerts/cert.pem')

        copytree(org_admin_home + '/msp/signcerts/', org_admin_home + '/msp/admincerts')

    # This line is extremely important, otherwise channel cannot be created
    os.environ['CORE_PEER_MSPCONFIGPATH'] = org_admin_home + '/msp'


# Switch to the current org's user identity.  Enroll if not previously enrolled.
def switchToUserIdentity(org_name, org):
    org_admin_home = org['admin_home']
    org_user_home = org['user_home']

    if not os.path.exists(org_user_home + '/msp'):
        # dowait('%(CA_NAME)s to start' % {'CA_NAME': org['ca']['name']},
        #        60,
        #        org['ca']['logfile'],
        #        [org['tls']['certfile']])

        sys.stdout.write('Enrolling user for organization %(org)s with home directory %(org_user_home)s...\n' % {
            'org': org_name,
            'org_user_home': org_user_home})
        sys.stdout.flush()

        os.environ['FABRIC_CA_CLIENT_HOME'] = org_user_home
        os.environ['FABRIC_CA_CLIENT_TLS_CERTFILES'] = org['tls']['certfile']

        data = {
            'USER_CREDENTIALS': '%(name)s:%(pass)s' % {
                'name': org['users']['user']['name'],
                'pass': org['users']['user']['pass'],
            },
            'CA_URL': '%(host)s:%(port)s' % {'host': org['ca']['host'], 'port': org['ca']['port']}
        }

        call(['fabric-ca-client', 'enroll', '-d', '-u', 'https://%(USER_CREDENTIALS)s@%(CA_URL)s' % data])

        # no intermediate cert in this config, delete generated files for not seeing warning
        sys.stdout.write('Delete intermediate certs in ' + org_user_home + '/msp' + '/intermediatecerts/\n')
        sys.stdout.flush()
        for file in os.listdir(org_user_home + '/msp' + '/intermediatecerts/'):
            file_path = os.path.join(org_user_home + '/msp' + '/intermediatecerts/', file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Set up admincerts directory if required
        copytree(org_admin_home + '/msp/signcerts/', org_user_home + '/msp/admincerts')

    os.environ['CORE_PEER_MSPCONFIGPATH'] = org_user_home + '/msp'