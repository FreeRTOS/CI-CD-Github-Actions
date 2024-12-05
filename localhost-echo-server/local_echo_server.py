#!/usr/bin/env python3

import asyncio
import logging
import os
from argparse import ArgumentParser

logger = logging.getLogger('echoserver')

async def echo_handler(reader, writer):
  address = writer.get_extra_info('peername')
  logger.debug('accept: %s', address)
  message = await reader.readline()
  writer.write(message)
  await writer.drain()
  writer.close()

if __name__ == '__main__':
  parser = ArgumentParser(description='Localhost Echo server.')
  parser.add_argument('--host',
                      type=str,
                      required=True,
                      help='Host address for the echo server.')
  parser.add_argument('--port_number',
                      type=int,
                      required=True,
                      help='Port for echo server.')
  args = parser.parse_args()
  logging.basicConfig()
  logger.setLevel(logging.DEBUG)
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  factory = asyncio.start_server(
    echo_handler,
    os.environ.get('HOST', args.host),
    os.environ.get('PORT', args.port_number)
  )
  server = loop.run_until_complete(factory)
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    pass
  server.close()
  loop.run_until_complete(server.wait_closed())
  loop.close()
