
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