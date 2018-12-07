## Playing with microservices, Docker, Python an Nameko

In the last projects that I've been involved with I've playing, in one way or another, with microservices, queues and things like that. I'm always facing the same tasks: Build RPCs, Workers, API gateways, ... Because of that I've searching one framework to help me with those such stuff. Finally I discover [Nameko](https://nameko.readthedocs.io/en/stable/). Basically Nameko is the Python tool that I've looking for. In this post I will create a simple Proof of concept to learn how to integrate Nameko within my projects. Let start.

The POC is a simple API gateway that gives me the localtime in iso format. I can create a simple Python script to do it

```python
import datetime
import time

print(datetime.datetime.fromtimestamp(time()).isoformat())
```

We also can create a simple Flask API server to consume this information. The idea is create a rpc worker to generate this information and also generate another worker to send the localtime but taken from a PostgreSQL database (yes I know it not very useful but it's just an excuse to use a PG database in the microservice)

We're going to create two rpc workers. One giving the local time:

```python
from nameko.rpc import rpc
from time import time
import datetime


class TimeService:
    name = "local_time_service"

    @rpc
    def local(self):
        return datetime.datetime.fromtimestamp(time()).isoformat()

```

And another one with the date from PostgreSQL:

```python
from nameko.rpc import rpc
from dotenv import load_dotenv
import os
from ext.pg import PgService

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path="{}/.env".format(current_dir))


class TimeService:
    name = "db_time_service"
    conn = PgService(os.getenv('DSN'))

    @rpc
    def db(self):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("select localtimestamp")
                timestamp = cur.fetchone()
        return timestamp[0]
```

I've created a service called PgService only to learn how to create dependency providers in nameko

```python
from nameko.extensions import DependencyProvider
import psycopg2


class PgService(DependencyProvider):

    def __init__(self, dsn):
        self.dsn = dsn

    def get_dependency(self, worker_ctx):
        return psycopg2.connect(self.dsn)
```

Now we only need to setup our flask api gateway

```python
from flask import Flask
from nameko.standalone.rpc import ServiceRpcProxy
from dotenv import load_dotenv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path="{}/.env".format(current_dir))

app = Flask(__name__)


def rpc_proxy(service):
    config = {'AMQP_URI': os.getenv('AMQP_URI')}
    return ServiceRpcProxy(service, config)


@app.route('/')
def hello():
    return "Hello"


@app.route('/local')
def local_time():
    with rpc_proxy('local_time_service') as rpc:
        time = rpc.local()

    return time


@app.route('/db')
def db_time():
    with rpc_proxy('db_time_service') as rpc:
        time = rpc.db()

    return time


if __name__ == '__main__':
    app.run()
```

As well as I wanna run my POC with docker, here the docker-compose file to set up the project

```yaml
version: '3.4'

services:
  api:
    image: nameko/api
    container_name: nameko.api
    hostname: api
    ports:
    - "8080:8080"
    restart: always
    links:
    - rabbit
    - db.worker
    - local.worker
    environment:
    - ENV=1
    - FLASK_APP=app.py
    - FLASK_DEBUG=1
    build:
      context: ./api
      dockerfile: .docker/Dockerfile-api
    #volumes:
    #- ./api:/usr/src/app:ro
    command: flask run --host=0.0.0.0 --port 8080
  db.worker:
    container_name: nameko.db.worker
    image: nameko/db.worker
    restart: always
    build:
      context: ./workers/db.worker
      dockerfile: .docker/Dockerfile-worker
    command: /bin/bash run.sh
  local.worker:
    container_name:  nameko.local.worker
    image: nameko/local.worker
    restart: always
    build:
      context: ./workers/local.worker
      dockerfile: .docker/Dockerfile-worker
    command: /bin/bash run.sh
  rabbit:
    container_name: nameko.rabbit
    image: rabbitmq:3-management
    restart: always
    ports:
    - "15672:15672"
    - "5672:5672"
    environment:
      RABBITMQ_ERLANG_COOKIE:
      RABBITMQ_DEFAULT_VHOST: /
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_DEFAULT_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_DEFAULT_PASS}
  pg:
    container_name: nameko.pg
    image: nameko/pg
    restart: always
    build:
      context: ./pg
      dockerfile: .docker/Dockerfile-pg
    #ports:
    #- "5432:5432"
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_DB: ${POSTGRES_DB}
      PGDATA: /var/lib/postgresql/data/pgdata
```

And that's all. Two nameko rpc services working together behind a api gateway
