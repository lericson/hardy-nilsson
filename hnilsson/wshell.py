import code
from hnilsson.worker import HardyWorkerConnection

def main(pid, cls=HardyWorkerConnection):
    w = cls(pid)
    w.config.setup_logging()
    g = {"w": w, "pid": pid}
    msg = ("Hardy Nilsson Interactive Queue Shell\n"
           "Use `w` to do things, it forwards to a queue.")
    code.interact(banner=msg, local=g)

if __name__ == "__main__":
    import sys
    main(sys.argv[1])  # arg1: pid of master
