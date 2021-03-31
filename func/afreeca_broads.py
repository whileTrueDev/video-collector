import requests 
import json
from datetime import datetime, timedelta

class AfreecaBroad:
    COLLECT_PERIOD = 2
    COLLECT_SIZE = 10 
    CLIENT_ID = None
    URL = 'https://openapi.afreecatv.com/broad/list' 

    def __init__(self, client_id):
        self.CLIENT_ID = client_id

    def get_broads(self, afreeca_target):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': '*/*'
        }

        params = {
            'client_id' : self.CLIENT_ID,
            'select_key': 'cate',
            'select_value' : '00040019',
            'order_type': 'broad_start',
            'page_no': 1
        }

        response = requests.get(self.URL, params= params, headers= headers)
        result = json.loads(response.text)

        boundary_time = datetime.now() - timedelta(minutes=self.COLLECT_PERIOD)
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
            response = requests.get(self.URL, params= params, headers= headers)
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
                if(user_id in afreeca_target):
                    target_broads.append(('afreeca', broad['user_id'], broad['broad_no']))
                
            else: 
                # time over
                break

        return target_broads