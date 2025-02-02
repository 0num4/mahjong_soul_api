import asyncio
import hashlib
import hmac
import logging
import random
import uuid
from optparse import OptionParser

import aiohttp
import dotenv
import os

from ms.base import MSRPCChannel
from ms.rpc import Lobby
import ms.protocol_pb2 as pb
from google.protobuf.json_format import MessageToJson

config = dotenv.load_dotenv()
print(os.environ["yostar_uid"])

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

MS_HOST = "https://game.mahjongsoul.com/"
PASSPORT_HOST = "https://passport.mahjongsoul.com/"


async def main():
    """
    Login to the CN server with username and password and get latest 30 game logs.
    """
    parser = OptionParser()
    parser.add_option("-u", "--username", type="string", help="Your account name.")
    parser.add_option("-p", "--password", type="string", help="Your account password.")
    parser.add_option("-l", "--log", type="string", help="Your log UUID for load.")

    opts, _ = parser.parse_args()
    username = opts.username
    password = opts.password
    log_uuid = opts.log

    # if not username or not password:
    #     parser.error("Username or password cant be empty")

    lobby, channel, version_to_force, accessTokenFromPassport = await connect()
    await login(lobby, username, password, version_to_force, accessTokenFromPassport)

    # https://github.com/kamicloud/mahjong-science-server/blob/master/conf/game_live.json
    gameLiveList = pb.ReqGameLiveList()
    gameLiveList.filter_id = 224  # 24: 3たまなん
    resGameLiveList = await lobby.fetch_game_live_list(gameLiveList)
    print(resGameLiveList)

    await channel.close()


async def connect():
    async with aiohttp.ClientSession() as session:
        async with session.get("{}/version.json".format(MS_HOST)) as res:
            version = await res.json()
            logging.info(f"Version: {version}")
            version = version["version"]
            version_to_force = version.replace(".w", "")

        async with session.get("{}/v{}/config.json".format(MS_HOST, version)) as res:
            config = await res.json()
            logging.info(f"Config: {config}")

            url = config["ip"][0]["region_urls"][0]["url"]
            passport_url = config["yo_service_url"][0]
            print(passport_url)

        async with session.get(url + "?service=ws-gateway&protocol=ws&ssl=true") as res:
            servers = await res.json()
            # mjjpgs.mahjongsoul.com:9663
            logging.info(f"Available servers: {servers}")

            servers = servers["servers"]
            server = random.choice(servers)
            endpoint = "wss://{}/gateway".format(server)

        async with session.post(
            passport_url + "/user/login/",
            data={
                "uid": os.environ["uid"],
                "token": os.environ["token"],
                "deviceId": f"web|{os.environ['uid']}",
            },
        ) as res:
            passport = await res.json()
            logging.info(f"Passport: {passport}")
            accessTokenFromPassport = passport["accessToken"]

    logging.info(f"Chosen endpoint: {endpoint}")
    channel = MSRPCChannel(endpoint)

    lobby = Lobby(channel)

    await channel.connect(MS_HOST)
    logging.info("Connection was established")

    return lobby, channel, version_to_force, accessTokenFromPassport


async def login(lobby, username, password, version_to_force, accessTokenFromPassport):
    logging.info("Login with username and password")

    # accessTokenの取得

    # req = pb.ReqLogin()
    # reqFromSoulLess = pb.ReqContestManageOauth2Auth()  # soulLessのtoken_kindがpermanent
    heartBeat = pb.ReqHeatBeat()
    heartBeat.no_operation_counter = 1
    hbRes = await lobby.heatbeat(heartBeat)  # hheartbeatはログインするまえに何回か動く
    print(hbRes)
    reqFromSoulLess = pb.ReqOauth2Auth()
    reqFromSoulLess.type = 7
    reqFromSoulLess.code = accessTokenFromPassport
    reqFromSoulLess.uid = os.environ["uid"]
    reqFromSoulLess.client_version_string = f"web-{version_to_force}"  # or version

    res = await lobby.oauth2_auth(reqFromSoulLess)

    token = res.access_token
    if not token:
        logging.error("Login Error:")
        logging.error(res)
        return False

    # reqOauth2Check = pb.ReqOauth2Check()
    # reqOauth2Check.type = 7
    # reqOauth2Check.access_token = token
    # resOauth2Check = await lobby.oauth2_check(reqOauth2Check)
    # print(resOauth2Check)  # 実機でもnullが帰ってくる
    # if not resOauth2Check.has_account:
    #     print("Invalid access token")
    #     return False

    reqOauth2Login = pb.ReqOauth2Login()
    reqOauth2Login.type = 7
    reqOauth2Login.access_token = token  # token  # 確認

    reqOauth2Login.reconnect = False
    reqOauth2Login.device.is_browser = True
    uuid_key = str(uuid.uuid1())
    print(uuid_key)
    reqOauth2Login.random_key = uuid_key
    reqOauth2Login.client_version_string = f"web-{version_to_force}"
    reqOauth2Login.gen_access_token = False
    reqOauth2Login.currency_platforms.append(2)

    resOauth2Login = await lobby.oauth2_login(reqOauth2Login)
    print(resOauth2Login)

    return True


async def load_game_logs(lobby):
    logging.info("Loading game logs")

    records = []
    current = 1
    step = 30
    req = pb.ReqGameRecordList()
    req.start = current
    req.count = step
    res = await lobby.fetch_game_record_list(req)
    records.extend([r.uuid for r in res.record_list])

    logging.info("Found {} records".format(len(records)))
    total = len(records)
    for i, r in enumerate(records):
        path = os.path.join("./", r)
        if os.path.exists(path):
            print("({}/{})Skipping existing {}".format(i + 1, total, i))
            continue

        req = pb.ReqGameRecord()
        req.game_uuid = r
        print("({}/{})Fetching {}".format(i + 1, total, r))
        res = await lobby.fetch_game_record(req)
        with open(path, "w") as f:
            print("({}/{})Saving {}".format(i + 1, total, r))
            f.write(MessageToJson(res))

    # await channel.close()
    clres = lobby._channel.close()
    print("Connection closed")
    print(clres)
    # await decode_records(records)

    return records


async def load_and_process_game_log(lobby, uuid, version_to_force):
    logging.info("Loading game log")

    req = pb.ReqGameRecord()
    req.game_uuid = uuid
    req.client_version_string = f"web-{version_to_force}"
    res = await lobby.fetch_game_record(req)

    record_wrapper = pb.Wrapper()
    record_wrapper.ParseFromString(res.data)

    game_details = pb.GameDetailRecords()
    game_details.ParseFromString(record_wrapper.data)

    game_records_count = len(game_details.records)
    logging.info("Found {} game records".format(game_records_count))

    round_record_wrapper = pb.Wrapper()
    is_show_new_round_record = False
    is_show_discard_tile = False
    is_show_deal_tile = False

    for i in range(0, game_records_count):
        round_record_wrapper.ParseFromString(game_details.records[i])

        if round_record_wrapper.name == ".lq.RecordNewRound" and not is_show_new_round_record:
            logging.info("Found record type = {}".format(round_record_wrapper.name))
            round_data = pb.RecordNewRound()
            round_data.ParseFromString(round_record_wrapper.data)
            print_data_as_json(round_data, "RecordNewRound")
            is_show_new_round_record = True

        if round_record_wrapper.name == ".lq.RecordDiscardTile" and not is_show_discard_tile:
            logging.info("Found record type = {}".format(round_record_wrapper.name))
            discard_tile = pb.RecordDiscardTile()
            discard_tile.ParseFromString(round_record_wrapper.data)
            print_data_as_json(discard_tile, "RecordDiscardTile")
            is_show_discard_tile = True

        if round_record_wrapper.name == ".lq.RecordDealTile" and not is_show_deal_tile:
            logging.info("Found record type = {}".format(round_record_wrapper.name))
            deal_tile = pb.RecordDealTile()
            deal_tile.ParseFromString(round_record_wrapper.data)
            print_data_as_json(deal_tile, "RecordDealTile")
            is_show_deal_tile = True

    return res


def print_data_as_json(data, type):
    json = MessageToJson(data)
    logging.info("{} json {}".format(type, json))


if __name__ == "__main__":
    asyncio.run(main())
