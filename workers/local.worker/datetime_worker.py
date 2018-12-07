from nameko.rpc import rpc
from time import time
import datetime


class TimeService:
    name = "local_time_service"

    @rpc
    def local(self):
        return datetime.datetime.fromtimestamp(time()).isoformat()
