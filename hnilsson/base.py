import logging

import beanstalkc
import irken
from irken.nicks import Mask
from irken.dispatch import DispatchRegistering, Command, handler
from irken.io import BaseIO

from hnilsson import load_config
from hnilsson.protocol import Job

logger = logging.getLogger("hnilsson.base")

class HardyQueueConsumer(DispatchRegistering):
    def __init__(self, conn, queue_conn=None):
        DispatchRegistering.__init__(self)
        self.conn = conn
        if not queue_conn:
            queue_conn = conn.make_queuer()
        self.queue_conn = queue_conn

    def run(self):
        self.running = True
        while self.running:
            qjob = self.queue_conn.reserve()
            try:
                self.recv_job(Job.from_str(qjob.body))
            except:
                qjob.bury()
                raise
            else:
                qjob.delete()

    def recv_job(self, job):
        ((prefix, command), args, kwds) = job
        source = self.conn.lookup_prefix(prefix)
        cmd = Command(command, source=source)
        if not self.dispatch(cmd, *args, **kwds):
            self.dispatch("hardy master default", cmd, args, kwds)

    @handler("hardy master default")
    def warn_unhandled(self, cmd, unhandled, args, kwds):
        logger.warn("unhandled job: %r", (unhandled, args, kwds))

class HardyMixin(object):
    make_io = BaseIO
    client_version = "hardy-nilsson"

    def __init__(self, nick, *args, **kwds):
        config = kwds.pop("config", None)
        if not config:
            config = load_config()
        self.config = config
        self.queue_conn = self.make_queuer()
        self.queue_consumer = self.make_queue_consumer()
        super(HardyMixin, self).__init__(nick, *args, **kwds)

    def make_queuer(self):
        c = self.config
        bs = beanstalkc.Connection(c.beanstalk_host, c.beanstalk_port)
        bs.use(self.queue_out_name)
        bs.watch(self.queue_in_name)
        return bs

    def make_queue_consumer(self):
        return HardyQueueConsumer(self)

    def send_job(self, job):
        logger.debug("send: %r", job)
        self.queue_conn.put(job.as_str())
