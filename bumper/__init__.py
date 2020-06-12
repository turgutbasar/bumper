#!/usr/bin/env python3

from bumper.webserver import WebServer
from bumper.xmppserver import XMPPServer
from bumper.models import *
from bumper.db import *
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

import importlib
import pkgutil


def strtobool(strbool):
    if str(strbool).lower() in ["true", "1", "t", "y", "on", "yes"]:
        return True
    else:
        return False


# os.environ['PYTHONASYNCIODEBUG'] = '1' # Uncomment to enable ASYNCIODEBUG
bumper_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Set defaults from environment variables first
# Folders
logs_dir = os.environ.get("BUMPER_LOGS") or os.path.join(bumper_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)  # Ensure logs directory exists or create
data_dir = os.environ.get("BUMPER_DATA") or os.path.join(bumper_dir, "data")
os.makedirs(data_dir, exist_ok=True)  # Ensure data directory exists or create
certs_dir = os.environ.get("BUMPER_CERTS") or os.path.join(bumper_dir, "certs")
os.makedirs(certs_dir, exist_ok=True)  # Ensure data directory exists or create


# Certs
ca_cert = os.environ.get("BUMPER_CA") or os.path.join(certs_dir, "ca.crt")
server_cert = os.environ.get("BUMPER_CERT") or os.path.join(certs_dir, "bumper.crt")
server_key = os.environ.get("BUMPER_KEY") or os.path.join(certs_dir, "bumper.key")

# Listeners
bumper_listen = "0.0.0.0"


bumper_announce_ip = os.environ.get("BUMPER_ANNOUNCE_IP") or bumper_listen

# Other
bumper_debug = strtobool(os.environ.get("BUMPER_DEBUG")) or False
use_auth = False
token_validity_seconds = 3600  # 1 hour
db = None

mqtt_server = None
mqtt_helperbot = None
conf_server = None
conf_server_2 = None
xmpp_server = None

# Plugins
sys.path.append(os.path.join(bumper_dir, "bumper", "plugins"))
sys.path.append(os.path.join(data_dir, "plugins"))

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg in pkgutil.iter_modules()
    if name.startswith('bumper_')
}

shutting_down = False

# Set format for all logs
logformat = logging.Formatter(
    "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(module)s :: %(funcName)s :: %(lineno)d :: %(message)s"
)

bumperlog = logging.getLogger("bumper")
bumper_rotate = RotatingFileHandler("logs/bumper.log", maxBytes=5000000, backupCount=5)
bumper_rotate.setFormatter(logformat)
bumperlog.addHandler(bumper_rotate)
# Override the logging level
# bumperlog.setLevel(logging.INFO)

confserverlog = logging.getLogger("confserver")
conf_rotate = RotatingFileHandler(
    "logs/confserver.log", maxBytes=5000000, backupCount=5
)
conf_rotate.setFormatter(logformat)
confserverlog.addHandler(conf_rotate)

boterrorlog = logging.getLogger("boterror")
boterrorlog_rotate = RotatingFileHandler(
    "logs/boterror.log", maxBytes=5000000, backupCount=5
)
boterrorlog_rotate.setFormatter(logformat)
boterrorlog.addHandler(boterrorlog_rotate)
# Override the logging level
# boterrorlog.setLevel(logging.INFO)

xmppserverlog = logging.getLogger("xmppserver")
xmpp_rotate = RotatingFileHandler(
    "logs/xmppserver.log", maxBytes=5000000, backupCount=5
)
xmpp_rotate.setFormatter(logformat)
xmppserverlog.addHandler(xmpp_rotate)
# Override the logging level
# xmppserverlog.setLevel(logging.INFO)

logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)  # Ignore this logger

xmpp_listen_port = 5223


# async def maintenance():
#     revoke_expired_tokens()
#
#
#
#
# def create_certs():
#     import platform
#     import os
#     import subprocess
#     import sys
#
#     path = os.path.dirname(sys.modules[__name__].__file__)
#     path = os.path.join(path, "..")
#     sys.path.insert(0, path)
#
#     print("Creating certificates")
#     odir = os.path.realpath(os.curdir)
#     os.chdir("certs")
#     if str(platform.system()).lower() == "windows":
#         # run for win
#         subprocess.run([os.path.join("..", "create_certs", "create_certs_windows.exe")])
#     elif str(platform.system()).lower() == "darwin":
#         # run on mac
#         subprocess.run([os.path.join("..", "create_certs", "create_certs_osx")])
#     elif str(platform.system()).lower() == "linux":
#         if "arm" in platform.machine().lower() or "aarch64" in platform.machine().lower():
#             # run for pi
#             subprocess.run([os.path.join("..", "create_certs", "create_certs_rpi")])
#         else:
#             # run for linux
#             subprocess.run([os.path.join("..", "create_certs", "create_certs_linux")])
#
#     else:
#         os.chdir(odir)
#         logging.log(
#             logging.FATAL,
#             "Can't determine platform. Create certs manually and try again.",
#         )
#         return
#
#     print("Certificates created")
#     os.chdir(odir)
#
#     if "__main__.py" in sys.argv[0]:
#         os.execv(
#             sys.executable, ["python", "-m", "bumper"] + sys.argv[1:]
#         )  # Start again
#
#     else:
#         os.execv(sys.executable, ["python"] + sys.argv)  # Start again
#
#
# def first_run():
#     create_certs()
#


class BumperFakeBotServer:
    def __init__(self, xmpp_addr, web_server):
        self.xmpp_server = XMPPServer(xmpp_addr)
        self.web_server = WebServer(web_server)

    async def run(self):
        # Start XMPP & web server
        await asyncio.gather(self.xmpp_server.start(), self.web_server.start())

    async def shutdown(self):
        await self.web_server.stop()
        self.xmpp_server.stop()
        bumperlog.info("Shutdown complete")


def main():
    # Init fake server with xmpp
    server = None
    loop = asyncio.get_event_loop()
    try:
        server = BumperFakeBotServer(("0.0.0.0", xmpp_listen_port), ("0.0.0.0", 8080))
        loop.run_until_complete(server.run())
    except KeyboardInterrupt:
        bumperlog.info("Shutting down...")
    finally:
        if server is not None:
            loop.run_until_complete(server.shutdown())

