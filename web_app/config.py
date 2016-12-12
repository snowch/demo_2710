import os, json

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string' 
    PORT = os.getenv('VCAP_APP_PORT', '5000')

    vcap_services = os.getenv("VCAP_SERVICES")
    if not vcap_services:
        raise BaseException(
                'Environment variable VCAP_SERVICES was not found.\n' +
                'VCAP_SERVICES must exist and contain the contents of the bluemix vcap.json data.'
                )

    vcap = json.loads(vcap_services)

    # Cloudant details

    cloudant_credentials = vcap['cloudantNoSQLDB'][0]['credentials']

    CL_HOST = cloudant_credentials['host']
    CL_USER = cloudant_credentials['username']
    CL_PASS = cloudant_credentials['password']
    CL_URL  = cloudant_credentials['url']

    CL_AUTH = ( CL_USER, CL_PASS )

    CL_MOVIEDB  = 'moviedb'
    CL_AUTHDB   = 'authdb'
    CL_RATINGDB = 'ratingdb'
    CL_RECOMMENDDB = 'recommendationdb'

    # Redis details

    redis_credentials = vcap['compose-for-redis'][0]['credentials']
    REDIS_URI = redis_credentials['uri']
    
    # Message Hub details
    
    mh_credentials = vcap['messagehub'][0]['credentials']
    
    MH_BROKERS_SASL = mh_credentials['kafka_brokers_sasl']
    MH_USER         = mh_credentials['user']
    MH_PASSWORD     = mh_credentials['password']
    MH_API_KEY      = mh_credentials['api_key']
    MH_ADMIN_URL    = mh_credentials['kafka_admin_url']
    MH_REST_URL     = mh_credentials['kafka_rest_url']
    
    MH_TOPIC_NAME   = 'recommender_app_events'

    @staticmethod
    def init_app(app):
        pass
