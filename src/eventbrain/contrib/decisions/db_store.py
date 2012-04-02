import logging
from datetime import datetime
from sqlalchemy import create_engine, \
        Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table

from eventbrain.decision.base import DecisionBase

LOG = logging.getLogger(__name__)


class DbStorage(DecisionBase):
    """
    A decision class to persist log data into
    a database storage. It logs all cpu:# logs
    """

    id = "cpu:#"

    def __init__(self, interval=10, threshold=90.0, **kwargs):
        if "db_name" not in kwargs and \
            "db_type" not in kwargs:
            LOG.error("Db name/type not specified!")
            return

        self.db_name = kwargs['db_name']
        self.db_type = kwargs['db_type']
        self.db_host = kwargs.get('db_host', 'localhost')
        self.db_port = kwargs.get('db_port', "")
        if self.db_port:
            self.db_port = ":%s" % self.db_port
        self.db_table = kwargs.get('db_table', 'logstorage')
        self.db_user = kwargs.get('db_user', '')
        self.db_pass = kwargs.get('db_pass', '')
        if (self.db_user):
            conn_string = "%s:%s@%s%s/%s" % (self.db_user,
                                           self.db_pass,
                                           self.db_host,
                                           self.db_port,
                                           self.db_name)
        else:
            conn_string = self.db_name
        conn_string = "%s://%s" % (self.db_type,
                                   conn_string)
        LOG.info("Connecting using %s" % conn_string)
        self.engine = create_engine(conn_string)
        self.session = sessionmaker(bind=self.engine)()

        meta = MetaData()
        Table(self.db_table, meta,
            Column('id', Integer, primary_key=True),
            Column('source', String(255)),
            Column('timestamp', DateTime, default=datetime.utcnow()),
            Column('listener', String(255)),
            Column('data', String(512)))

        Base = declarative_base()
        
        class Log(Base):
            __table__ = meta.tables[self.db_table]

            def __repr__(self):
                return "%s/%s/%s/%s" % (self.sender,
                                        self.listener,
                                        self.timestamp,
                                        self.data)

        self.table = Log
        if 'reset_table' in kwargs.keys() and kwargs['reset_table']:
            meta.drop_all(bind=self.engine)
        meta.create_all(bind=self.engine)
        super(DbStorage, self).__init__(interval, 
                                       threshold, 
                                       None, **kwargs)

    def on_update(self, sender, data, **kwargs):
        LOG.info("Received data from %s:[%s] : %s" % (self.id,
                                                   sender,
                                                   data))
        try:
            log = self.table()
            log.sender = sender
            log.listener = self.id
            log.timestamp = datetime.utcnow()
            log.data = unicode(data)
            LOG.info("Saving %s" % log)
            self.session.add(log)
            self.session.commit()
        except Exception, ex:
            self.session.rollback()
            LOG.exception(ex)

    def clean(self):
        #clean resources on disconnect
        LOG.info("Unloading resources")
        self.session.close()
