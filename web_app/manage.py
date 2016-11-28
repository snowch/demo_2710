from flask.ext.script import Manager, Server
from app import app
import config
from db_setup import delete_dbs, create_dbs

port = app.config['PORT']
server = Server(host="0.0.0.0", port=port)

manager = Manager(app)
manager.add_command("runserver", server)

@manager.command
def db_clean_setup():
    "Delete and re-create existing Cloudant databases"
    delete_dbs()
    create_dbs()

@manager.command
def db_setup():
    "Create cloudant database"
    create_dbs()

if app.debug:
    # debug routes
    for rule in app.url_map.iter_rules():
        print(rule.endpoint, rule)

if __name__ == '__main__':
    manager.run()
