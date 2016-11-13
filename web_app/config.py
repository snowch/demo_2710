import os, json

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string' 
    PORT = os.getenv('VCAP_APP_PORT', '5000')

    try:
        vcap = json.loads(os.getenv("VCAP_SERVICES"))['cloudantNoSQLDB']
    except:
        raise BaseException(
            'A Cloudant service is not bound to the application.\n' +
            'Please bind a Cloudant service and try again.'
            )

    CL_USER = vcap[0]['credentials']['username']
    CL_PASS = vcap[0]['credentials']['password']
    CL_URL  = vcap[0]['credentials']['url']
    CL_AUTH = ( CL_USER, CL_PASS )

    CL_MUSICDB  = 'musicdb'
    CL_AUTHDB   = 'authdb'
    CL_RATINGDB = 'ratingdb'

    @staticmethod
    def init_app(app):
        pass
