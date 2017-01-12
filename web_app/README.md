### Setup

My local environment is python-3.5.0.  Older python versions will not work.

#### Setup the source code

```
git clone https://github.com/snowch/demo_2710
cd demo_2710/web_app
source venv/bin/activate
pip3.5 install -r requirements.txt
```

#### Configure Cloudant and Redis

 - Create a Cloudant and Redis service in Bluemix.
 - Create the file etc/cloudant_vcap.json (see cloudant_vcap.json_template)
 - Create the file etc/redis_vcap.json (see redis.json_template)


#### Setup the databases

```
./run.sh db_all
```

### Run locally

```
./run.sh
```

### Push to bluemix

 - edit manifest.yml
   - provide a unique host
   - change the name of the services to reflect
     - your cloudant service name
     - your redis service name

Then run

```
cf login ...
cf push
```

### To create recommendations

 - create an account in the webapp
 - rate some movies
 - create a new DSX project, then 
   - upload the Cloudant+Recommender+Pyspark.ipynb notebook
   - follow the instructions to setup the cloudant_credentials.json file
   - click: Cell -> run all
 - when finished, navigate back to the web application and click on 'Get Recommendations'

### Developing

You can run python code from the python REPL, e.g.


```
$ cd web_app
$ export VCAP_SERVICES="{$(cat etc/cloudant_vcap.json),$(cat etc/redis_vcap.json)}"
$ python3.5
>>> from app.dao import DAO
>>> DAO.get_movie_names([1,2,3])
{1: 'Toy Story (1995)', 2: 'Jumanji (1995)', 3: 'Grumpier Old Men (1995)'}
>>>
```
