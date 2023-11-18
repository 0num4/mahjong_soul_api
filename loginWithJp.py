import asyncio
import hashlib
import hmac
import logging
import os
import random
import uuid
from optparse import OptionParser
import dotenv

import aiohttp

from ms.base import MSRPCChannel
from ms.rpc import Lobby
import ms.protocol_pb2 as pb
from google.protobuf.json_format import MessageToJson


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

MS_HOST = "https://game.mahjongsoul.com/"
PASSPORT_HOST = "https://passport.mahjongsoul.com/"

config = dotenv.load_dotenv()
print(os.environ["yostar_uid"])
