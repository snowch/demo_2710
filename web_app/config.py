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

    try:
        vcap = json.loads(vcap_services)['cloudantNoSQLDB']
    except:
        raise BaseException(
            'A cloudantNoSQLDB element was not found in the vcap.json.\n' +
            'If you are running on Bluemix, do you have a Cloudant database service bound to this application?'
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
