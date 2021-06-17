from multiprocessing.connection import Listener
from datetime import datetime
from multiprocessing import Pool, cpu_count, Manager
from func.sl_cli import get_video

address = ('localhost', 6309)     # family is deduced to be 'AF_INET'


def broad_update(lock, new_broad_list, now_broad_list):
    now_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('[{}] broadcasting : {}'.format(now_date, now_broad_list.keys()))
    new_broads = []

    # async - await
    for platform, user_id, broad_no in new_broad_list:

        # new broad check
        if not user_id in now_broad_list.keys():
            new_broads.append((platform, user_id, broad_no, lock, now_broad_list))

    return new_broads


if __name__ == '__main__':
    # shared resource
    with Manager() as manager:
        lock = manager.Lock()
        now_broad_list = manager.dict()

        # process pool
        with Pool(processes=cpu_count()-1) as pool:
            # signal listener
            with Listener(address, authkey=b'onad') as listener:
                # infinity process
                while True:
                    try:
                        # connection success
                        with listener.accept() as conn:
                            new_broad_list = conn.recv()
                            broads = broad_update(lock, new_broad_list, now_broad_list)
                            if not len(broads) == 0:
                                pool.imap_unordered(get_video, broads)

                    except EOFError:
                        print('connection error')