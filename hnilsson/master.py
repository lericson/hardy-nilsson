import os
import threading

import irken
from irken.dispatch import handler

from hnilsson.base import HardyMixin, HardyQueueConsumer
from hnilsson.protocol import Job

class HardyMasterQueueConsumer(HardyQueueConsumer):
    @handler("hardy send-cmd")
    def forward_send_cmd(self, cmd, fw_cmd, fw_args=(), fw_kwds={}):
        if fw_kwds:
            raise ValueError("cannot forward keyword arguments")
        prefix, cmd = fw_cmd
        self.conn.send_cmd(prefix, cmd, fw_args)

class HardyMaster(irken.BaseMixin, HardyMixin):
    queue_out_name = "workers"
    queue_in_name = "master"

    def __init__(self, nick, *args, **kwds):
        self.pid = os.getpid()
        self.queue_out_name += "-%d" % self.pid
        self.queue_in_name += "-%d" % self.pid
        super(HardyMaster, self).__init__(nick, *args, **kwds)

    def dispatch(self, cmd, *args, **kwds):
        rv = super(HardyMaster, self).dispatch(cmd, *args, **kwds)
        prefix = getattr(cmd, "source", None)
        job = Job((prefix, cmd), args, kwds)
        self.send_job(job)
        return rv + 1

    def make_queue_consumer(self):
        consumer = HardyMasterQueueConsumer(self)
        thread = threading.Thread(target=consumer.run)
        thread.setDaemon(True)
        consumer.start = thread.start
        return consumer

    def run(self):
        self.queue_consumer.start()
        return super(HardyMaster, self).run()

    def stop(self):
        self.queue_consumer.running = False

bases = (HardyMaster,) + irken.bases
from irken.ctcp import CTCPDispatchMixin, BaseCTCPDispatchMixin
bs_mp = {CTCPDispatchMixin: None}
bases = tuple(bs_mp.get(b, b) for b in bases if bs_mp.get(b, b))
HardyMasterConnection = type("HardyMasterConnection", bases, {})

def main(cls=HardyMasterConnection):
    from hnilsson import load_config
    cnf = load_config()
    cnf.setup_logging()
    reginfo = (cnf.irc_username, cnf.irc_realname)
    m = cls(nick=cnf.irc_nick, autoregister=reginfo, config=cnf)
    m.connect(cnf.irc_server)
    try:
        m.run()
    finally:
        m.stop()

if __name__ == "__main__":
    main()
