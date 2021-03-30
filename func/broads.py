import requests 
import json
from datetime import datetime, timedelta

collect_target = [
'1004suna',
'120510',
'ad1yn2',
'anfdksrud96',
'arinbbidol',
'asa0921',
'b13246',
'barams01',
'bht0205',
'bhw2209',
'byflash',
'ch1716',
'cinnamoroll',
'ckmin706',
'dlghfjs',
'drumkyn',
'dudadi770',
'eldehd96',
'freshtomato',
'galsa',
'gjgj3274',
'gks2wl',
'gksdidqksxn',
'ioioiobb',
'joey1114',
'killgusdnk',
'leetk0410',
'love91911',
'mm3mmm',
'moonwol0614',
'nila25',
'ogm0905',
'partypeople',
'phonics1',
'pi0314',
'rlatmdgus',
'rrvv17',
'rudals5467',
'sccha21',
'seokwngud',
'superbsw123',
'wnnw',
'wnstn0905',
'y1026',
'yuambo',
'zkwks4413',
'chlwlals88',
'cnsgkcnehd74'
]


def get_broad_url():
    urls = []
    COLLECT_PERIOD = 2
    COLLECT_SIZE = 10

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*'
    }

    params = {
        'client_id' : "e515195dfe0c6cf7eb2e7bfe05ab582e",
        'select_key': 'cate',
        'select_value' : '00040019',
        # 'order_type': 'broad_start',
        'page_no': 1
    }

    URL = 'https://openapi.afreecatv.com/broad/list' 
    response = requests.get(URL, params= params, headers= headers)
    result = json.loads(response.text)

    boundary_time = datetime.now() - timedelta(minutes=COLLECT_PERIOD)

    # error handling
    if not result.get('total_cnt'):
        return []

    total_cnt = result.get('total_cnt') 
    pages = int(total_cnt / 60) + 1
    pages = 3 if pages >= 3 else pages

    if not result.get('broad'):
        return []
    
    # pagination
    broad_list = result.get('broad') 

    # page < 2 -> error
    for i in range(2, pages + 1):
        params['page_no'] = i
        response = requests.get(URL, params= params, headers= headers)
        result = json.loads(response.text)

        if result.get('broad'):
            new_broad_list = result.get('broad')
            broad_list.extend(new_broad_list)
        
    # check broad start time
    target_broads = []
    for broad in broad_list:
        broad_time_text = broad.get('broad_start')
        user_id = broad.get('user_id')
        broad_time = datetime.strptime(broad_time_text, '%Y-%m-%d %H:%M:%S')
        if(broad_time >= boundary_time):
            
            # target creator check
            if(user_id in collect_target):
                target_broads.append((broad['user_id'], broad['broad_no']))
            
        else: 
            # time over
            break

    return target_broads

if __name__ == '__main__':
    print(get_broad_url())
