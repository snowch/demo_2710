import requests, json
import atexit
import redis
from . import app

redis = redis.StrictRedis.from_url(app.config['REDIS_URI'])

def get_next_user_id():
    return redis.hincrby('app_ids', 'user_id')

@atexit.register
def python_shutting_down():
    print('Disconnecting redist client')
    # TODO




