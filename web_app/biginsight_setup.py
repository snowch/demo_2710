import paramiko
import json

class SshUtil:
        
    def __init__(self):
        
        with open('./biginsight_credentials.json') as data_file:
            credentials = json.load(data_file)
        
        hostname = credentials['hostname']
        username = credentials['username']
        password = credentials['password']
        
        #### start patching crypto ####
        # Monkey patches cryptography's backend detection.
        from cryptography.hazmat import backends
        try:
            from cryptography.hazmat.backends.commoncrypto.backend import backend as be_cc
        except ImportError:
            be_cc = None

        try:
            from cryptography.hazmat.backends.openssl.backend import backend as be_ossl
        except ImportError:
            be_ossl = None

        backends._available_backends_list = [ be for be in (be_cc, be_ossl) if be is not None ]
        #### end patching crypto ####
        
        s = paramiko.SSHClient()
        s.load_system_host_keys()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        self.client = s
        self.hostname = hostname
        self.username = username
        self.password = password
    
    def cmd(self, command): 
        self.client.connect(self.hostname, 22, self.username, self.password)
        # kinit will fail on Basic clusters, but that can be ignored
        self.client.exec_command('kinit -k -t {0}.keytab {0}@IBM.COM'.format(self.username))
        (stdin, stdout, stderr) = self.client.exec_command(command)
        for line in stdout.readlines():
            print(line.rstrip())
        for line in stderr.readlines():
            print(line.rstrip())
        self.client.close()

def setup_spark():
    
    ssh = SshUtil()
    ssh.cmd('ls -l .')