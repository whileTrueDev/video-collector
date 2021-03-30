from multiprocessing.connection import Client
from func.broads import get_broad_url
import schedule
import time

address = ('localhost', 6309)

DEBUG = True

def signal_listener():
    try:
        with Client(address, authkey=b'onad') as conn:
            # async - await
            broads = get_broad_url()
            conn.send(broads)
    except ConnectionRefusedError :
        print('connection refused')

if __name__ == '__main__':
    if DEBUG :
        signal_listener()
    else:
        schedule.every(2).minutes.do(signal_listener)

        while True:
            schedule.run_pending()
            time.sleep(1)