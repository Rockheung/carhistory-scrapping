import copy
import asyncio
import aiohttp
import os
import json
from functools import partial
from bs4 import BeautifulSoup

DEV_MODE = True
if DEV_MODE and not os.path.exists('.pages'):
    os.mkdir('.pages')

CH_HOSTNAME = 'https://www.carhistory.or.kr'
_CH_HOSTNAME = 'http://127.0.0.1:4000'
COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Host': 'www.carhistory.or.kr',
    'Origin': 'https://www.carhistory.or.kr',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,la;q=0.6'
}

DEFAULT_CAR_BODY = {
    
}

def gen_ch_url(step):
    return f'{CH_HOSTNAME}/damoa/mobile/{step}.car'

def gen_car_info_query(**params):
    return {
        "car_num": params['car_num'],
        "ins_car_name": params['car_name'],
        "ins_car_name_code": params['ins_car_name_code'],
        "ins_car_name_code_type": params['ins_car_name_code_type'],
        "ins_car_made_ym": params['prod_year'],
        "cMaker": params['car_maker'],
        "cName": params['car_name'],
        "cNameDtl": params['car_name_dtl'],
        "cOpt": params['car_opt']
    }

def get_default_from_options(**params):
    return {
        param[0]: param[1] \
            if not isinstance(param[1], list) \
            else param[1][0] \
                for param in params.items()
    }


def get_cookie(raw_headers):
    set_cookies_values = [raw_header[1].decode('utf-8').split(';')[0] \
        for raw_header in raw_headers \
        if raw_header[0] == b'Set-Cookie' or raw_header[0] == b'set-cookie']

    # 키가 중복인 쿠키가 날아온다. 이를 제거하기 위함.
    cookies_dict = {key_value.split('=')[0]:key_value.split('=')[1] \
        for key_value in set_cookies_values}
    # cookie = '; '.join(["=".join(cookie_item) for cookie_item in cookies_dict.items()])
    
    return cookies_dict


async def fetch(client, step):
    async with client.get(gen_ch_url(step)) as resp:
        assert resp.status == 200
        html = await resp.text()
        cookies = get_cookie(resp.raw_headers)
        if DEV_MODE:
            with open(f'.pages/{step}.html', 'w') as f:
                f.write(html)

        return html, cookies


async def submit(client, cookie, step, referer, **params):
    form_data = aiohttp.FormData(fields=params)
    _headers = dict()
    _headers['Referer'] = gen_ch_url(referer)
    _headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    
    async with client.post(gen_ch_url(step), headers=_headers, data=form_data, cookies=cookie) as resp:
        html = await resp.text()
        if 'text/html' in resp.headers.get('content-type'):
            if DEV_MODE:
                with open(f'.pages/{step}.html', 'w') as f:
                    f.write(html)
            return html
        elif 'text/json' in resp.headers.get('content-type'):
            try :
                assert resp.status == 200
                return json.loads(html)
            except json.decoder.JSONDecodeError :
                # step1_set_car_info_json_malformed
                # {
                #   "result":"1",
                #   "list":carhistory.damoa.bean.ConditionInfo@3684b5c2,
                #   "ip":"114.201.54.130"
                # }
                # 정상적인 JSON이 들어오지 않아 파싱이 되지 않는다.
                if 'carhistory.damoa.bean.ConditionInfo' in html:
                    return dict({'result': '1'})
                else: 
                    raise json.decoder.JSONDecodeError
        else :
            raise Exception

def gen_cookie_from_key(key):
    return {
        'JSESSIONID' : f'{key}.kidich2_servlet_engine6'
    }

json_dump_kr = partial(json.dumps, ensure_ascii=False)
