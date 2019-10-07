import asyncio, aiohttp
from parser import *
from helper import *

async def step1_get_hidden_values(client):
    html, cookies = await fetch(client, 'step1')
    soup = BeautifulSoup(html, 'html5lib')

    req_cba_form = soup.select('form#reqCBAForm input[type="hidden"]')
    values = {input['name']: input['value'] \
        for input in req_cba_form if len(input['value']) > 0}

    return values, cookies

async def step1_srch_kidi_car_info_json(client, cookie, **query):
    query['type'] = 'srchKidiCarInfo'
    car_data = await submit(client, cookie, 'searchCarData', 'step1', **query)
    assert car_data['result'] == '1'
    return car_data['list']


async def step1_set_car_info_json_malformed(client, cookie, **query):
    query_transformed = gen_car_info_query(**query)
    query_transformed['type'] = 'setCarInfo'
    print(query)
    print(query_transformed)
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
    values = {input['name']: input['value'] \
        for input in s_form \
            if len(input['value']) > 0}

    return values

async def step2(client, cookie, **query):
    html = await submit(client, cookie, 'step2', 'newPostProc', **query)

    soup = BeautifulSoup(html, 'html5lib')

    info_form_hidden = soup.select('form#infoForm > input[type=hidden]')

    values = {input.get('name'): input.get('value') \
        for input in info_form_hidden \
            if input.get('name')}

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

async def step3(client, cookie, **query):
    html = await submit(client, cookie, 'step3', 'step2', **query)
    soup = BeautifulSoup(html, 'html5lib')

    insu_table_type01_rows = soup.select('table.insu_table_type01 tbody > tr')
    # print(insu_table_type01_rows)
    _first_one = {insu_table_type01_rows[0].select('td.citem')[0].string:insu_table_type01_rows[0].select('td.total_cost > span')[0].string.strip()}
    _from_second = {insu_item.select('td.citem')[0].string : insu_item.select('td.total_cost')[0].string.strip() for insu_item in insu_table_type01_rows[1:]}

    return {**_first_one, **_from_second}
