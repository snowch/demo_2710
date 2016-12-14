from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import ssl
import requests
import json
import atexit

from . import app

producer = None

def setup_producer():

    bootstrap_servers   = app.config['MH_BROKERS_SASL']
    sasl_plain_username = app.config['MH_USER']
    sasl_plain_password = app.config['MH_PASSWORD']

    sasl_mechanism = 'PLAIN'
    security_protocol = 'SASL_SSL'

    # Create a new context using system defaults, disable all but TLS1.2
    context = ssl.create_default_context()
    context.options &= ssl.OP_NO_TLSv1
    context.options &= ssl.OP_NO_TLSv1_1

    producer = KafkaProducer(bootstrap_servers = bootstrap_servers,
                             sasl_plain_username = sasl_plain_username,
                             sasl_plain_password = sasl_plain_password,
                             security_protocol = security_protocol,
                             ssl_context = context,
                             sasl_mechanism = sasl_mechanism,
                             api_version = (0,10),
                             batch_size = 0,
                             retries = 10)

    return producer

producer = setup_producer()


def setup_consumer():

    bootstrap_servers     = app.config['MH_BROKERS_SASL']
    sasl_plain_username   = app.config['MH_USER']
    sasl_plain_password   = app.config['MH_PASSWORD']
    messagehub_topic_name = app.config['MH_TOPIC_NAME']
    
    sasl_mechanism = 'PLAIN'
    security_protocol = 'SASL_SSL'

    # Create a new context using system defaults, disable all but TLS1.2
    context = ssl.create_default_context()
    context.options &= ssl.OP_NO_TLSv1
    context.options &= ssl.OP_NO_TLSv1_1

    consumer = KafkaConsumer(messagehub_topic_name,
                             bootstrap_servers = bootstrap_servers,
                             sasl_plain_username = sasl_plain_username,
                             sasl_plain_password = sasl_plain_password,
                             security_protocol = security_protocol,
                             ssl_context = context,
                             sasl_mechanism = sasl_mechanism,
                             api_version = (0,10),
                             consumer_timeout_ms = 10000,
                             auto_offset_reset = 'earliest',
                             enable_auto_commit=False,
                             group_id = None
                            )
    return consumer

consumer = setup_consumer()

def peek_messages():

    try:
        for message in consumer:
            print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                  message.offset, message.key,
                                                  message.value))
    except Exception as e:
        print("No messages found:", str(e))

def create_topic_if_required():
    
    data = { 
        'name' : app.config['MH_TOPIC_NAME'],
        'configs'  : { 
            'retentionMs': 3600000 # 1 hour (this is the minimum)
        }
    }
    headers = {
        'content-type': 'application/json',
        'X-Auth-Token' : app.config['MH_API_KEY']
    }
    url = app.config['MH_ADMIN_URL'] + '/admin/topics'
    
    # response = requests.delete(url + '/' + app.config['MH_TOPIC_NAME'], headers = headers)
    # print('deleting topic', response.text)
    
    # create the topic (http POST)
    response = requests.post(url, headers = headers, data = json.dumps(data))
    # print('creating topic', response.text)
    
create_topic_if_required()

def send(message):
    print('sending {0} to {1}'.format(message, app.config['MH_TOPIC_NAME']))
    try:
        result = producer.send(app.config['MH_TOPIC_NAME'], message.encode())
        print(result)
        result = producer.flush()
        print()
    except Exception as e:
        print("Couldn't send message:", str(e))

@atexit.register
def python_shutting_down():
    print('Disconnecting kafka client')
    try:
        consumer.close()
    except Exception as e:
        print("Problem closing consumer:", str(e))
    
    try:
        producer.close(10)
    except Exception as e:
        print("Problem closing producer:", str(e))
