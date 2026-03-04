import logging
import asyncio
import os
import socket
from argparse import ArgumentParser
from amqtt.broker import Broker

logger = logging.getLogger(__name__)

LOCAL_HOST_IP = socket.gethostbyname("localhost")

# Parse passed in credentials
parser = ArgumentParser(description='Localhost MQTT broker.')

parser.add_argument('--host',
                    type=str,
                    required=True,
                    help='Host address for the echo server.')
parser.add_argument('--root-ca-cert-path',
                    type=str,
                    required=True,
                    help='Path to the root CA certificate.')
parser.add_argument('--server-cert-path',
                    type=str,
                    required=True,
                    help='Path to the server certificate.')
parser.add_argument('--server-priv-key-path',
                    type=str,
                    required=True,
                    help='Path to the private key')
args = parser.parse_args()

# Broker configuration
config = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": f"{args.host}:1883",
            "max_connections": 1000,
        },
        "tls": {
            "type": "tcp",
            "bind": f"{args.host}:8883",
            "max_connections": 1000,
            "ssl": True,
            "cafile": args.root_ca_cert_path,
            "certfile": args.server_cert_path,
            "keyfile": args.server_priv_key_path,
        },
    },
    "timeout_disconnect_delay": 0,
    "plugins": {
        "amqtt.plugins.logging_amqtt.EventLoggerPlugin": {},
        "amqtt.plugins.logging_amqtt.PacketLoggerPlugin": {},
        "amqtt.plugins.authentication.AnonymousAuthPlugin": {
            "allow_anonymous": True
        },
        "amqtt.plugins.authentication.FileAuthPlugin": {
            "password_file": os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "passwd"
            )
        },
        "amqtt.plugins.sys.broker.BrokerSysPlugin": {
            "sys_interval": 10
        },
    },
}

async def broker_coroutine():
    broker = Broker(config)
    await broker.start()

if __name__ == "__main__":
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)

    # Start the MQTT broker
    asyncio.get_event_loop().run_until_complete(broker_coroutine())
    asyncio.get_event_loop().run_forever()
