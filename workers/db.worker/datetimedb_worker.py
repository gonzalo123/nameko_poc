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
