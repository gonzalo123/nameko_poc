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
