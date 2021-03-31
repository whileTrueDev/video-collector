from multiprocessing.connection import Client
import schedule
import time
import os
from func.afreeca_broads import AfreecaBroad
from func.twitch_broads import TwitchBroad
from targets import twitch_target, afreeca_target

from dotenv import load_dotenv
load_dotenv(verbose=True)

class BroadClient:
    _twitch_collector = None
    _afreeca_collector = None
    _address = ('localhost', 6309)
    _DEBUG = False

    def __init__(self):
        self._twitch_collector = TwitchBroad(os.getenv('TWITCH_CLIENT'), os.getenv('TWITCH_PW'))
        self._afreeca_collector = AfreecaBroad(os.getenv('AFREECA_CLIENT'))


    def signal(self):
        broads = []
        # get broads twitch, afreeca
        broads.extend(self._twitch_collector.get_broads(twitch_target))
        broads.extend(self._afreeca_collector.get_broads(afreeca_target)) 
        try:
            with Client(self._address, authkey=b'onad') as conn:
                # async - await
                conn.send(broads)
        except ConnectionRefusedError :
            print('connection refused')

    def process(self):
        if self._DEBUG :
            self.signal()
        else:
            schedule.every(2).minutes.do(self.signal)

            while True:
                schedule.run_pending()
                time.sleep(1)


if __name__ == '__main__':
    # object to send signal to listener 
    client = BroadClient()

    client.process()
  