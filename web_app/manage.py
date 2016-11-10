from flask.ext.script import Manager, Server
from app import app
import os

port = os.getenv('VCAP_APP_PORT', '5000')
server = Server(host="0.0.0.0", port=port)

manager = Manager(app)
manager.add_command("runserver", server)


if __name__ == '__main__':
    manager.run()
