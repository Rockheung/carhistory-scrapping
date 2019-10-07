import asyncio, aiohttp
from aiohttp import web
import json

# from parser import *
from helper import gen_cookie_from_key, json_dump_kr, gen_car_info_query
# from handler import *

from main import *

routes = web.RouteTableDef()



# session key로 사용할 해쉬를 받아옴, 이후 모든 요청의 쿼리스트링에 포함시킴.
@routes.get('/session')
async def get_key(request):
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        cookie = await get_new_cookie(session)
        
        return web.json_response({"key": cookie['JSESSIONID'].split('.')[0]})


##########################searchCarInfo#############################



# 바로 차량번호로 검색
@routes.get('/car')
async def get_car_info(request):
    cookie = gen_cookie_from_key(request.query['key'])
    query = dict(car_num=request.query['num'])
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        srch_kidi_car_info = await step1_srch_kidi_car_info_json(session, cookie, **query)
        return aiohttp.web.json_response(srch_kidi_car_info[0],dumps=json_dump_kr)


# 해당 세션에 차량 정보 저장
@routes.post('/car')
async def set_car_info(request):
    cookie = gen_cookie_from_key(request.query['key'])
    data = await request.json()
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        await step1_set_car_info_json_malformed(session, cookie, **data)
        return aiohttp.web.Response(status=201)
        
    

SEARCH_QUERY = {
    'car_maker': '',
    'car_name': '',
    'prod_year': '',
    'car_name_dtl': '',
    'car_opt': ''
}

# 차량 제조사
@routes.get('/car/maker')
async def car_maker(request):
    cookie = gen_cookie_from_key(request.query['key'])
    query = dict({'type':'car_maker'},**SEARCH_QUERY)
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        car_data = await submit(session, cookie, 'searchCarData', 'step1', **query)
        assert car_data['result'] == '1'
        return web.json_response(car_data['list'],dumps=json_dump_kr)


@routes.get('/car/name')
async def car_name(request):
    cookie = gen_cookie_from_key(request.query['key'])
    query = dict({'type':'car_name'},**SEARCH_QUERY)
    query.update({
        'car_maker':request.query['car_maker']
    })
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        car_data = await submit(session, cookie, 'searchCarData', 'step1', **query)
        assert car_data['result'] == '1'
        return web.json_response(car_data['list'],dumps=json_dump_kr)


@routes.get('/car/year')
async def prod_year(request):
    cookie = gen_cookie_from_key(request.query['key'])
    query = dict({'type':'prod_year'},**SEARCH_QUERY)
    query.update({
        'car_maker':request.query['car_maker'],
        'car_name':request.query['car_name']
    })
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        car_data = await submit(session, cookie, 'searchCarData', 'step1', **query)
        assert car_data['result'] == '1'
        return web.json_response(car_data['list'],dumps=json_dump_kr)


@routes.get('/car/detail')
async def car_name_dtl(request):
    cookie = gen_cookie_from_key(request.query['key'])
    query = dict({'type':'car_name_dtl'},**SEARCH_QUERY)
    query.update({
        'car_maker':request.query['car_maker'],
        'car_name':request.query['car_name'],
        'prod_year':request.query['prod_year']
    })
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        car_data = await submit(session, cookie, 'searchCarData', 'step1', **query)
        assert car_data['result'] == '1'
        return web.json_response(car_data['list'],dumps=json_dump_kr)


@routes.get('/car/options')
async def car_options(request):
    cookie = gen_cookie_from_key(request.query['key'])
    query = dict({'type':'car_opt'}, **SEARCH_QUERY)
    query.update({
        'car_maker':request.query['car_maker'],
        'car_name':request.query['car_name'],
        'prod_year':request.query['prod_year'],
        'car_name_dtl':request.query['car_name_dtl']
    })
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        car_data = await submit(session, cookie, 'searchCarData', 'step1', **query)
        assert car_data['result'] == '1'
        return web.json_response(car_data['list'],dumps=json_dump_kr)




##########################humanVerify#############################

@routes.post('/auth')
async def get_sms_num(request):
    cookie = gen_cookie_from_key(request.query['key'])
    data = await request.json()
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        req_cba_form = await step1_get_hidden_values(session, cookie)
        # print(req_cba_form)
        req_pcc_result_form = await step1_phone_verify_values(session, cookie, **data, **req_cba_form)
        # print(req_pcc_result_form)
        auth_chunk = {
            'reqInfo': req_pcc_result_form["reqInfo"],
            'reqNum': req_pcc_result_form["reqNum"],
            'confirmSeq': req_pcc_result_form["confirmSeq"]
        }

        return aiohttp.web.json_response(auth_chunk,dumps=json_dump_kr)


@routes.put('/auth')
async def verify_sms_num(request):
    cookie = gen_cookie_from_key(request.query['key'])
    data = await request.json()
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        s_form = await step1_phone_sms_submit(session, cookie, **data)
        return aiohttp.web.Response(status=201)


@routes.get('/options')
async def get_insu_options(request):
    cookie = gen_cookie_from_key(request.query['key'])
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        insu_options = await step2_get_hidden_values(session, cookie)
        del insu_options["ssn1"]
        del insu_options["ssn2"]
        del insu_options["authType"]
        del insu_options["userCi"]
        del insu_options["kniaSsn"]
        del insu_options["carInfoSeq"]
        del insu_options["contInfoSeq"]
        del insu_options["carPlateGubun"]
        del insu_options["carPlateAgentCode"]
        del insu_options["carPlateNo"]
        del insu_options["orgCd"]
        del insu_options["insTypeCode"]
        del insu_options["insContNo"]
        del insu_options["ins_car_name"]
        del insu_options["ins_car_name_code"]
        del insu_options["ins_car_name_code_type"]
        del insu_options["ins_car_made_ym"]
        del insu_options["ins_begin_date"]
        del insu_options["ins_end_date"]
        del insu_options["car_use_type"]
        return aiohttp.web.json_response(insu_options,dumps=json_dump_kr)


@routes.post('/options')
async def set_insu_options(request):
    cookie = gen_cookie_from_key(request.query['key'])
    data = await request.json()
    insu_submit_data = {**data}
    insu_submit_data['special2YYYY'] = data['special2Opt1'][0:4] if data['special2Opt1'] != '000000' else ''
    insu_submit_data['special2MM'] = data['special2Opt1'][4:6] if data['special2Opt1'] != '000000' else ''
    insu_submit_data['special2Opt2'] = data['special2Opt3'] if data['special2Opt3'] != '000' else ''
    insu_submit_data['special3YYYY'] = data['special3Opt'][0:4] if data['special3Opt'] != '00000000' else ''
    insu_submit_data['special3MM'] = data['special3Opt'][4:6] if data['special3Opt'] != '00000000' else ''
    insu_submit_data['special3DD'] = data['special3Opt'][6:8] if data['special3Opt'] != '00000000' else ''

    if insu_submit_data['special5Yn'] == '0':
        if 'special5Opt3' in insu_submit_data:
            del insu_submit_data['special5Opt3'] 
        if 'special5Opt2' in insu_submit_data:
            del insu_submit_data['special5Opt2']

    elif insu_submit_data['driverScope'] == '3':
        insu_submit_data['sepcial5Opt3'] = insu_submit_data['sepcial5Opt']
        if 'special5Opt2' in insu_submit_data:
            del insu_submit_data['special5Opt2']
    
    elif insu_submit_data['driverScope'] == '2':
        insu_submit_data['sepcial5Opt2'] = insu_submit_data['sepcial5Opt']
        if 'special5Opt3' in insu_submit_data:
            del insu_submit_data['special5Opt3'] 

    else :
        insu_submit_data['special5Yn'] = '0'
        insu_submit_data['special5Opt'] = '000'

        if 'special5Opt3' in insu_submit_data:
            del insu_submit_data['special5Opt3'] 
        if 'special5Opt2' in insu_submit_data:
            del insu_submit_data['special5Opt2']

    
    async with aiohttp.ClientSession(headers=COMMON_HEADERS) as session:
        
        info_form_options = await step2_get_hidden_values(session, cookie)
        default_options = get_default_from_options(**info_form_options)
    
        is_2000 = True if default_options['ssn2'][0] in ['3','4','7','8'] else False

        _override_options = {
            'driverDthAmt' : '3000',
            'driverInjAmt' : '1500',
            'minBrith': f'{"20" if is_2000 else "19"}{default_options["ssn1"]}',
            'minBrithY': f'{"20" if is_2000 else "19"}{default_options["ssn1"][0:2]}',
            'minBrithM': f'{default_options["ssn1"][2:4]}',
            'minBrithD': f'{default_options["ssn1"][4:6]}'
        }



        insu_data = {**default_options, **_override_options, **insu_submit_data}
        # print(insu_data)


        # await asyncio.sleep(60)


        insu_result = await step3(session, cookie, **insu_submit_data)

        return aiohttp.web.json_response(insu_result,dumps=json_dump_kr)
