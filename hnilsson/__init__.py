import os
from os.path import dirname as dn, join as jn
import pyconf

package_dir = dn(__file__)
container_dir = dn(package_dir)
default_config_path = jn(container_dir, "config.py")

def load_config(default_path=default_config_path):
    rv = pyconf.load(os.environ.get("HNILSSON_CONF", default_config_path))
    def setup_logging():
        import logging
        logging.basicConfig(**rv.log_opts)
    rv.setup_logging = setup_logging
    return rv
