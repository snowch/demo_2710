from kafka import KafkaProducer
from kafka.errors import KafkaError
import ssl
import requests
import json

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
                             api_version = (0,10))

    return producer

producer = setup_producer()

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
    
    # TODO remove this for production environments
    response = requests.delete(url + '/' + app.config['MH_TOPIC_NAME'], headers = headers)
    print(response.text)
    
    # create the topic (http POST)
    response = requests.post(url, headers = headers, data = json.dumps(data))
    print(response.text)
    
create_topic_if_required()

def send(message):
    producer.send(app.config['MH_TOPIC_NAME'], message.encode())
    producer.flush()
    