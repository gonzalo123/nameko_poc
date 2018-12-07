from nameko.extensions import DependencyProvider
import psycopg2


class PgService(DependencyProvider):

    def __init__(self, dsn):
        self.dsn = dsn

    def get_dependency(self, worker_ctx):
        return psycopg2.connect(self.dsn)
