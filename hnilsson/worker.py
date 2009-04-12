import logging
from irken.dispatch import handler

from hnilsson.base import HardyConnection, HardyQueueConsumer
from hnilsson.protocol import Job

logger = logging.getLogger("hnilsson.worker")

#print "dispatch %s(%s)" % (args[0].replace(" ", "_"), ", ".join(__import__("itertools").chain(iter(map(repr, args[1:])), ("%s=%r" % i for i in kwds.items()))))

class HardyWorkerQueueConsumer(HardyQueueConsumer):
    def __init__(self, conn):
        # Tell superclass to use the same connection for the consumption part
        # as the sending part.
        super(HardyWorkerQueueConsumer, self).__init__(conn, conn.queue_conn)

    def dispatch(self, cmd, *args, **kwds):
        return self.conn.dispatch(cmd, *args, **kwds)

class HardyWorker(HardyConnection):
    make_io = staticmethod(lambda: None)
    make_queue_consumer = lambda self: HardyWorkerQueueConsumer(self)
    queue_out_name = "master"
    queue_in_name = "workers"

    def __init__(self, pid, *args, **kwds):
        self.pid = str(pid)
        self.queue_out_name += "-" + self.pid
        self.queue_in_name += "-" + self.pid
        super(HardyWorker, self).__init__(None, *args, **kwds)

    def run(self):
        return self.queue_consumer.run()

    def send_cmd(self, prefix, command, args):
        job = Job((None, "hardy send-cmd"), Job((prefix, command), args, {}))
        self.send_job(job)

    def dispatch(self, *args, **kwds):
        return super(HardyWorker, self).dispatch(*args, **kwds) + 1

    @handler("irc cmd privmsg")
    def hello_world(self, cmd, target_name, text):
        cmd.source.i = getattr(cmd.source, "i", 0) + 1
        print cmd.source, cmd.source.i, text

def main(pid, cls=HardyWorker):
    w = cls(pid)
    w.config.setup_logging()
    w.run()

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
