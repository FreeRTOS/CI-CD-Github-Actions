import logging
import asyncio
import os
import socket
from amqtt.broker import Broker

logger = logging.getLogger(__name__)

LOCAL_HOST_IP = socket.gethostbyname("localhost")

# File names for credentials
ROOT_CA_CERT_FILE = "root_ca_cert.crt"
SERVER_PRIV_KEY_FILE = "server_priv_key.key"
SERVER_CERT_FILE = "server_cert.crt"

# Broker configuration
config = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": f"{LOCAL_HOST_IP}:1883",
        },
        "tls": {
            "type": "tcp",
            "bind": f"{LOCAL_HOST_IP}:8883",
            "ssl": "on",
            "cafile": ROOT_CA_CERT_FILE,
            "certfile": SERVER_CERT_FILE,
            "keyfile": SERVER_PRIV_KEY_FILE,
        },
    },
    "sys_interval": 10,
    "auth": {
        "allow-anonymous": True,
        "password-file": os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "passwd"
        ),
        "plugins": ["auth_anonymous"],
    },
    "topic-check": {
        "enabled": True,
        "plugins": []
    },
}

broker = Broker(config)

async def broker_coroutine():
    await broker.start()

if __name__ == "__main__":
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)

    # Start the MQTT broker
    asyncio.get_event_loop().run_until_complete(broker_coroutine())
    asyncio.get_event_loop().run_forever()