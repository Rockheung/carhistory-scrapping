import copy
import asyncio
import aiohttp
import os
import json
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

DUMMY_DATA =  {
    'car_num': '48도9842'
}

USER = {
    'birth': '19901125',
    'hpno': '01071349409',
    'gender': 'M',
    'name': '박흥준',
    'fgnGbn': '1',
    'ssn1': '901125',
    'ssn2': '1034746',
    'hpcorp': 'LGM',
    'number': '010',
    'number2': '7134',
    'number3': '9409'
}



## 미구현: 문자 재발송. 이때는 SCI평가정보를 거쳐서 날아오는 듯 싶다
# https://www.carhistory.or.kr/selfcheck/mobile/reqSmsRetry.ajax
# reqInfo: A1A1FF494D4328DFCD66FF8748208FD79CFE1A8B5A4530B9DF8333F8562FF26B069F6F9DCF7F0F383E328AFEF50AA55CDEEC43D1CF7093FDBF81D468F5BD2658626D99DC148C06CB861BDB59BD3BC162DA2E50496A3CD6E6AC5B8B73ECC88116662FEBE618A37CCF6424E87D7E8CF3FB57027E6B7B1F90C14F734A2B637E595EB53D1A42CFCA0A343C297BE538FD566E
# reqNum: '201909241644553333333333                '

def gen_ch_url(step):
    return f'{CH_HOSTNAME}/damoa/mobile/{step}.car'

def gen_car_info_query(**params):
    return {
        "car_num": params['car_num'] if 'car_num' in params else '', 
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
    cookie = '; '.join(["=".join(cookie_item) for cookie_item in cookies_dict.items()])
    
    return cookies_dict


def driver_inj_gubun_handler(div_b1, next=None, **options):
    # 모든 타입은 문자열
    # { 
    #   driverInjGubun: [ 1, 2, 3 ],
    #   driverDthAmt: [
    #     [1500, 3000, 5000, 10000],
    #     [10000, 10000, 20000, 20000],
    #     ['']
    #   ],
    #   driverInjAmt: [
    #     [1500, 1500, 1500, 1500],
    #     [2000, 3000, 2000, 3000],
    #     ['']
    #   ]
    # }
    radio_name = div_b1.select('div.panel span.radio > input[type="radio"]')[0].get('name')

    for radio_input in div_b1.select('div.panel span.radio > input[type="radio"]'):
        options[radio_name] = [] \
            if radio_name not in options \
            else options[radio_name]

        if radio_input.has_attr('checked'):
            options[radio_name].insert(0, radio_input.get('value'))
        else :
            options[radio_name].append(radio_input.get('value'))

    options[radio_name] = list(options[radio_name])

    driverDthAmt_selects = div_b1.select('div.panel span.multi_c2 > select')
    options['driverDthAmt'] \
        = [[option.get('value').split('/')[0] \
            for option in select.select('option') \
                if len(option.get('value'))] \
                    for select in driverDthAmt_selects]
    options['driverDthAmt'].append([''])

    options['driverInjAmt'] \
        = [[option.get('value').split('/')[1] \
            for option in select.select('option') \
                if len(option.get('value'))] \
                    for select in driverDthAmt_selects]
    options['driverInjAmt'].append([''])

    if next:
        return next(div_b1, None, **options)

    else :
        return options



def driver_scope_min_birth_handler(div_b1, next=None, **options):
    
    min_birth_input = div_b1.select('div.panel > p > input[type="hidden"]')[0]
    options[min_birth_input.get('name')] = min_birth_input.get('value')

    for select in div_b1.select('div.panel > p > select'):
        for option in select.select('option'):
            options[select.get('name')] = [] \
                if select.get('name') not in options \
                else options[select.get('name')]
            options[select.get('name')].append(option.get('value'))
    
    if next:
        return next(div_b1, None, **options)

    else :
        return options


def special_1_opt_handler(div_b1, next=None, **options):

    special_1_select = div_b1.select('div.panel > div > p > select')[0]
    options[special_1_select.get('name')] = [option.get('value') \
        for option in special_1_select.select('option')]


    if next:
        return next(div_b1, None, **options)

    else :
        return options



def special_2_opt_handler(div_b1, next=None, **options):

    special_2_inputs = div_b1.select('div.panel div > input[type="hidden"]')
    options[special_2_inputs[0].get('name')] = '000000' \
        if not special_2_inputs[0].get('value') \
        else special_2_inputs[0].get('value')
    options[special_2_inputs[1].get('name')] = '000' \
        if not special_2_inputs[1].get('value') \
        else special_2_inputs[1].get('value')

    for select in div_b1.select('div.panel div > p > select'):
        for opt in select.select('option'):
            options[select.get('name')] = [] \
                if select.get('name') not in options \
                else options[select.get('name')]
            options[select.get('name')].append(opt.get('value'))

    special_2_text_input = div_b1.select('div.panel div > p > input[type="text"]')[0]
    options[special_2_text_input.get('name')] = '000' \
        if not special_2_text_input.get('value') \
        else special_2_text_input.get('value')
    
    if next:
        return next(div_b1, None, **options)

    else :
        return options


def special_3_opt_handler(div_b1, next=None, **options):

    special_3_child_opt_name = div_b1.select('div.panel > div > p > span > input[checked="checked"]')[0].get('name')
    special_3_child_options = div_b1.select('div.panel > div > p > span > input')
    options[special_3_child_opt_name] = [opt.get('value') \
        for opt in special_3_child_options]

    special_3_opt_yyyymmdd = div_b1.select('div.panel > div > p > input[type="hidden"]')[0]
    options[special_3_opt_yyyymmdd.get('name')] = '00000000' \
        if not special_3_opt_yyyymmdd.get('value') \
        else special_3_opt_yyyymmdd.get('value')

    for select in div_b1.select('div.panel > div select'):
        for option in select.select('option'):
            options[select.get('name')] = [] \
                if select.get('name') not in options \
                    else options[select.get('name')]
            options[select.get('name')].append(option.get('value'))
    
    if next:
        return next(div_b1, None, **options)

    else :
        return options


def special_5_opt_handler(div_b1, next=None, **options):
    
    special_5_opt = div_b1.select('div.panel > div > input[type="hidden"]')[0]
    options[special_5_opt.get('name')] = '000' \
        if not special_5_opt.get('value') \
        else special_5_opt.get('value')

    for view in div_b1.select('div.panel > div > div[id^=view]'):
        for _input in view.select('span.radio input[type="radio"]'):
            options[_input.get('name')] = [] \
                if _input.get('name') not in options \
                else options[_input.get('name')]
            options[_input.get('name')].append(_input.get('value'))

    if next:
        return next(div_b1, None, **options)

    else :
        return options


def special_6_opt_handler(div_b1, next=None, **options):

    special_6_opt = div_b1.select('div.panel > div > p > input[type="text"]')[0]
    options[special_6_opt.get('name')] = '000' \
        if not special_6_opt.get('value') \
        else special_6_opt.get('value')

    if next:
        return next(div_b1, None, **options)

    else :
        return options


def special_7_opt_handler(div_b1, next=None, **options):

    special_7_opt_limit = div_b1.select('div.panel > div > input[type="hidden"]')[0]

    options[special_7_opt_limit.get('name')] = special_7_opt_limit.get('value')

    for text_input in div_b1.select('div.panel > div > p > input[type="text"]'):
        options[text_input.get('name')] = '00000' \
            if not text_input.get('value') \
            else text_input.get('value')

    if next:
        return next(div_b1, None, **options)

    else :
        return options

def simple_selector_options(div_b1, next=None, **options):
    spans = div_b1.select('div.panel > p > span.radio')
    radio_inputs = div_b1.select('div.panel > p > span.radio > input')
    if not radio_inputs:
        # 자기신체손해: driverInjGubun은 다음 파싱으로 넘겨야 한다..
        return next(div_b1, None, **options)
    name = radio_inputs[0].get('name')
    if not name:
        # 대인배상 I: psn1Yn은 필수 선택이다, name도 없고 파싱할 것도 없다.
        return options
    options[name] = [] if name not in options else options[name]

    for span in spans:
        
        if span.select('input')[0].has_attr('checked'):
            options[name].insert(0, span.select('input')[0].get('value'))
        else :
            options[name].append(span.select('input')[0].get('value'))

    options[name] = list(options[name])

    if next:
        return next(div_b1, None, **options)

    else:
        return options


async def fetch(client, cookie, step):
    async with client.get(gen_ch_url(step), cookies=cookie) as resp:
        assert resp.status == 200
        html = await resp.text()
        if DEV_MODE:
            with open(f'.pages/{step}.html', 'w') as f:
                f.write(html)

        return html


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


async def get_new_cookie(client):
    url = 'https://www.carhistory.or.kr/setDevice.ajax'
    headers = {
        **COMMON_HEADERS,
        **({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    }
    data = b'device=android'
    async with client.post(url, headers=headers, data=data) as resp:
        return get_cookie(resp.raw_headers)

async def step1_get_hidden_values(client, cookie):
    html = await fetch(client, cookie, 'step1')
    soup = BeautifulSoup(html, 'html5lib')

    req_cba_form = soup.select('form#reqCBAForm input[type="hidden"]')
    values = {_input['name']: _input['value'] \
        for _input in req_cba_form if len(_input['value']) > 0}

    return values

async def step1_srch_kidi_car_info_json(client, cookie, **query):
    query['type'] = 'srchKidiCarInfo'
    car_data = await submit(client, cookie, 'searchCarData', 'step1', **query)
    assert car_data['result'] == '1'
    return car_data['list']


async def step1_set_car_info_json_malformed(client, cookie, **query):
    query_transformed = gen_car_info_query(**query)
    query_transformed['type'] = 'setCarInfo'
    set_car_result = await submit(client, cookie, 'searchCarData', 'step1', **query_transformed)
    assert set_car_result['result'] == '1'
    return set_car_result


async def step1_phone_verify_values(client, cookie, **query):
    html = await submit(client, cookie, 'preProc', 'step1', **query)
    soup = BeautifulSoup(html, 'html5lib')
    
    req_pcc_result_form = soup.select('form[name="reqPCCResultForm"] input[type="hidden"]')
    values = {_input['name']: _input['value'] \
        for _input in req_pcc_result_form \
            if _input['value']}

    # req_pcc_sms_retry_form = soup.select('form#reqPCCSMSRetryForm input[type="hidden"]')
    # values = {f're{input["name"]}': input['value'] for input in req_pcc_sms_retry_form if len(input['value']) > 0}

    return values

async def step1_phone_sms_submit(client, cookie, **query):
    html = await submit(client, cookie, 'newPostProc', 'preProc', **query)
    soup = BeautifulSoup(html, 'html5lib')

    s_form = soup.select('form[name="sForm"] input[type="hidden"]')
    values = {_input['name']: _input['value'] \
        for _input in s_form \
            if len(_input['value']) > 0}

    return values


def step2_parser(html) :
    soup = BeautifulSoup(html, 'html5lib')

    info_form_hidden = soup.select('form#infoForm > input[type=hidden]')

    values = {_input.get('name'): _input.get('value') \
        for _input in info_form_hidden \
            if _input.get('name')}

    insu_selects = soup.select('form#infoForm div.b1')


    # 대인배상 I
    values = {**values, **simple_selector_options(insu_selects[0])}

    # 대인배상 II
    values = {**values, **simple_selector_options(insu_selects[1])}

    # 대물배상
    values = {**values, **simple_selector_options(insu_selects[2])}

    # 자기신체손해
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[3], 
            driver_inj_gubun_handler
        )
    }

    # 무보험차상해
    values = {**values, **simple_selector_options(insu_selects[4])}

    # 자기차량손해
    values = {**values, **simple_selector_options(insu_selects[5])}

    # 긴급출동 서비스
    values = {**values, **simple_selector_options(insu_selects[6])}

    # 물적사고 할증금액
    values = {**values, **simple_selector_options(insu_selects[7])}

    # 운전자 범위
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[8], 
            driver_scope_min_birth_handler
        )
    }

    # 마일리지 할인
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[9], 
            special_1_opt_handler
        )
    }

    # 블랙박스 할인
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[10], 
            special_2_opt_handler
        )
    }

    # 자녀할인
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[11], 
            special_3_opt_handler
        )
    }

    # 사고통보장치 할인
    values = {**values, **simple_selector_options(insu_selects[12])}

    # 대중교통 할인
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[13], 
            special_5_opt_handler
        )
    }

    # 안전운전습관 할인
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[14], 
            special_6_opt_handler
        )
    }

    # 과거주행거리연동 할인
    values = {
        **values, 
        **simple_selector_options(
            insu_selects[15], 
            special_7_opt_handler
        )
    }

    # E-MAIL 할인
    values = {**values, **simple_selector_options(insu_selects[16])}

    # 서민우대 할인
    values = {**values, **simple_selector_options(insu_selects[17])}

    return values

async def step2(client, cookie, **query):
    html = await submit(client, cookie, 'step2', 'newPostProc', **query)
    return step2_parser(html)

async def step2_get_hidden_values(client, cookie):
    html = await fetch(client, cookie, 'step2')
    return step2_parser(html)


async def step3(client, cookie, **query):
    html = await submit(client, cookie, 'step3', 'step2', **query)
    soup = BeautifulSoup(html, 'html5lib')

    insu_table_type01_rows = soup.select('table.insu_table_type01 tbody > tr')
    # print(insu_table_type01_rows)
    _first_one = {
        'insu_company_name': insu_table_type01_rows[0].select('td.citem')[0].string,
        'insu_total_cost': insu_table_type01_rows[0].select('td.total_cost > span')[0].string.strip(),
        'insu_link': insu_table_type01_rows[0].select('td > a')[0].get('href')
    }
    _from_second = [
        {
            'insu_company_name': insu_item.select('td.citem')[0].string,
            'insu_total_cost': insu_item.select('td.total_cost')[0].string.strip(),
            'insu_link': insu_item.select('td > a')[0].get('href')
        } for insu_item in insu_table_type01_rows[1:]
    ]

    return [_first_one, *_from_second]


async def main():
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        cookie = await get_new_cookie(session)
        req_cba_form = await step1_get_hidden_values(session, cookie)
        # print(req_cba_form)

        srch_kidi_car_info = await step1_srch_kidi_car_info_json(session, cookie, car_num=DUMMY_DATA['car_num'])
        # print(car_data)

        set_car_result = await step1_set_car_info_json_malformed(session, cookie, **srch_kidi_car_info[0], car_num=DUMMY_DATA['car_num'])
        # print(set_car_result)

        req_pcc_result_form = await step1_phone_verify_values(session, cookie, **USER, **req_cba_form)
        # print(req_pcc_result_form)

        # print(session.cookie_jar)
        s_form = await step1_phone_sms_submit(session, cookie, **req_pcc_result_form, smsnum=input('인증문자: '))
        # print(s_form)

        info_form_options = await step2(session, cookie, **s_form)
        # print(info_form_options)

        defaults_options = get_default_from_options(**info_form_options)

        _override_options = {
            'driverDthAmt' : '3000', 
            'driverInjAmt' : '1500',
            'minBrith': f'19{defaults_options["ssn1"]}',
            'minBrithY': f'19{defaults_options["ssn1"][0:2]}',
            'minBrithM': f'{defaults_options["ssn1"][2:4]}',
            'minBrithD': f'{defaults_options["ssn1"][4:6]}'
        }

        if defaults_options['special5Yn'] == '0':
            del defaults_options['special5Opt3']
            del defaults_options['special5Opt2']

        elif defaults_options['driverScope'] == '3':
            del defaults_options['special5Opt2']
        
        elif defaults_options['driverScope'] == '2':
            del defaults_options['special5Opt3']

        insu_submit_data = {**defaults_options, **_override_options}
        print(insu_submit_data)


        # await asyncio.sleep(60)


        insu_result = await step3(session, cookie, **insu_submit_data)

        print(insu_result)

        return
        # html = await fetch(session, 'step1')
        # print(html)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # Wait 250 ms for the underlying SSL connections to close
    # loop.run_until_complete(asyncio.sleep(0.250))
    # loop.close()
