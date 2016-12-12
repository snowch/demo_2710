import paramiko
import json
import re
from app import app
        
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
    
    def exec_command(self, command):
        self.client.connect(self.hostname, 22, self.username, self.password)
        # kinit will fail on Basic clusters, but that can be ignored
        self.client.exec_command('kinit -k -t {0}.keytab {0}@IBM.COM'.format(self.username))
        return self.client.exec_command(command)    
    
    def cmd_print(self, command): 
        (stdin, stdout, stderr) = self.exec_command(command)
        for line in stdout.readlines():
            print(line.rstrip())
        for line in stderr.readlines():
            print(line.rstrip())
        self.client.close()

    def put(self, filenames):
        from scp import SCPClient
        self.client.connect(self.hostname, 22, self.username, self.password)
        # kinit will fail on Basic clusters, but that can be ignored
        self.client.exec_command('kinit -k -t {0}.keytab {0}@IBM.COM'.format(self.username))
        with SCPClient(self.client.get_transport()) as scp:
            scp.put(filenames)
        scp.close()

def setup_spark():
    
    ssh = SshUtil()
    (stdin, stdout, stderr) = ssh.exec_command('yarn application -list')
    
    for line in stdout.readlines():
        if re.search("^application_", line.rstrip()):
            yarn_app = line.split()
            if yarn_app[1] == "MovieRating":
                ssh.cmd_print("yarn application -kill {0}".format(yarn_app[0]))
                
    
    jar_file = '../scala_streaming_predictor_with_cloudant/movie-rating_2.10-1.0.jar'
    
    import os  
    if not os.path.isfile(jar_file):
        raise BaseException("Couldn't find {0}. Inspect the README in the project for build instructions".format(jar_file))
                
    ssh.put(jar_file)
    
    ssh.cmd_print("""
       echo 'spark.bootstrap_servers={0}'     > spark_streaming.conf
       echo 'spark.sasl_username={1}'         >> spark_streaming.conf
       echo 'spark.sasl_password={2}'         >> spark_streaming.conf
       echo 'spark.messagehub_topic_name={3}' >> spark_streaming.conf
       echo 'spark.api_key={4}'               >> spark_streaming.conf
       echo 'spark.kafka_rest_url={5}'        >> spark_streaming.conf
       echo 'spark.cloudant_host={6}'         >> spark_streaming.conf
       echo 'spark.cloudant_user={7}'         >> spark_streaming.conf
       echo 'spark.cloudant_password={8}'     >> spark_streaming.conf
       
       cat /usr/iop/current/spark-client/conf/spark-defaults.conf >> spark_streaming.conf
    """.format(
        ",".join(app.config['MH_BROKERS_SASL']),
        app.config['MH_USER'],
        app.config['MH_PASSWORD'],
        app.config['MH_TOPIC_NAME'],
        app.config['MH_API_KEY'],
        app.config['MH_REST_URL'],
        app.config['CL_HOST'],
        app.config['CL_USER'],
        app.config['CL_PASS']
    ))
    
    # for debugging ...
    # ssh.cmd_print("cat spark_streaming.conf")

    ssh.cmd_print("""
        echo 'log4j.rootLogger=INFO, rolling'                                            >  log4j-spark.properties
        echo 'log4j.appender.rolling=org.apache.log4j.RollingFileAppender'               >> log4j-spark.properties
        echo 'log4j.appender.rolling.layout=org.apache.log4j.PatternLayout'              >> log4j-spark.properties
        echo 'log4j.appender.rolling.layout.conversionPattern=[%d] %p %m (%c)%n'         >> log4j-spark.properties
        echo 'log4j.appender.rolling.immediateFlush=true'                                >> log4j-spark.properties
        echo 'log4j.appender.rolling.maxFileSize=50MB'                                   >> log4j-spark.properties
        echo 'log4j.appender.rolling.maxBackupIndex=5'                                   >> log4j-spark.properties
        echo 'log4j.appender.rolling.file=${spark.yarn.app.container.log.dir}/spark.log' >> log4j-spark.properties
        echo 'log4j.appender.rolling.encoding=UTF-8'                                     >> log4j-spark.properties
        echo 'log4j.logger.org.apache.spark=WARN'                                        >> log4j-spark.properties
        echo 'log4j.logger.org.eclipse.jetty=WARN'                                       >> log4j-spark.properties
    """)
    
    ssh.cmd_print('''
         spark-submit --class "MovieRating" \
             --master yarn \
             --deploy-mode cluster \
             --properties-file spark_streaming.conf \
             --files ${HOME}/log4j-spark.properties \
             --conf "spark.driver.extraJavaOptions=-Dlog4j.configuration=log4j-spark.properties" \
             --conf "spark.driver.extraJavaOptions=-Diop.version=4.2.0.0" \
             --conf "spark.executor.extraJavaOptions=-Dlog4j.configuration=log4j-spark.properties" \
             --packages cloudant-labs:spark-cloudant:1.6.4-s_2.10 \
             ./movie-rating_2.10-1.0.jar > /dev/null 2>&1 &
         ''')

    # ssh.cmd_print('''
    #     spark-submit --class "MovieRating" \
    #         --properties-file spark_streaming.conf \
    #         --packages cloudant-labs:spark-cloudant:1.6.4-s_2.10 \
    #         ./movie-rating_2.10-1.0.jar > spark.log 2>&1 &
    #     ''')

    (stdin, stdout, stderr) = ssh.exec_command('sleep 5 && yarn application -list')
    
    for line in stdout.readlines():
        if re.search("^application_", line.rstrip()):
            yarn_app = line.split()
            if yarn_app[1] == "MovieRating":
                ssh.cmd_print("yarn logs -applicationId {0}".format(yarn_app[0]))
