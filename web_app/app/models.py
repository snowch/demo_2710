import os, json
import requests
from . import app

class Albums:

    @staticmethod
    def find_albums(name):

        qry = { 
            "selector": {
              "$text": name
            }
        }
        response = requests.post(app.config['CL_URL'] + '/musicdb/_find', 
                    auth=app.config['CL_AUTH'], 
                    data=json.dumps(qry), 
                    headers={'Content-Type':'application/json'})

        return json.loads(response.text)['docs']

