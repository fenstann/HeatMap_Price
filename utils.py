import requests
from bs4 import BeautifulSoup
from json import loads
from user_agent import generate_user_agent, generate_navigator
from random import randint
from time import sleep
import re
from datetime import date, timedelta


def addData(request):
    get_url = City.objects.values('url', 'pk')
    types = ['vtorichka', 'novostroyka']
    for type in types:
        if type == 'novostroyka':
            new = True
        else:
            new = False
        for x in get_url:
            id_city = x['pk'] #Текущий id города
            url_city = x['url']
            max_page = get_page_nubmer(url_city, type)


            print(max_page)
            for page in range(1, max_page):
                stopnumber = 0
                if stopnumber >= 40:
                    break
                else:
                    print(url_city)
                    print(page)

                    allinfo = get_page(url_city, page, type)
                    if not allinfo:
                        allinfo = get_page(url_city, page, type)
                    print(len(allinfo))

                    #Проверка на дубли
                    norepeatInfo = []
                    for info in allinfo:
                        check_id = SellList.objects.filter(pk=info['idAvito'],fullPriceRub = info['price'] ).exists()
                        if check_id == False :
                            #allinfo.remove(info)
                            norepeatInfo.append(info)
                        else:
                            stopnumber +=0

                    #Получаем данные с полных страниц
                    print(len(norepeatInfo))

                    start_time = time.time()
                    fullInfo = get_full_page(norepeatInfo)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    test = SellList.objects.count()
                    for item in fullInfo:
                       

                        if  SellList.objects.filter(pk=item['id_avito'],fullPriceRub = item['fullPriceRUB']).exists() == True:
                            print('Было')

                        try:
                            id_buildings, buildStatus = Buildings.objects.get_or_create(typeOfHouse_id=item['house_type'],
                                                                 totalFloor=item['total_floor'], lat=item['adress_lat'],
                                                                 lng=item['adress_lon'])
                        except Buildings.MultipleObjectsReturned:
                            id_buildings = Buildings.objects.filter(typeOfHouse_id=item['house_type'],
                                                                    totalFloor=item['total_floor'],
                                                                    lat=item['adress_lat'],
                                                                    lng=item['adress_lon']).first()
                        # СОхраняем в SellList
                        row = SellList(idAvito=item['id_avito'], cityName_id=id_city,
                                       room_id=item['room'], fullPriceRub=item['fullPriceRUB'],
                                       fullPriceDollars=item['fullPriceUSD'], priceForMetres=item['priceForMetres'],
                                       agent=item['agent'], floor=item['floor'], building_id=id_buildings.pk,
                                       novostroy=new, area=item['area'], areaKitchen=item['area_kitchen'],
                                       dateAdd=item['date'], areaLive=item['area_live'], description=item['description']

                                       )
                        row.save_base(raw=True)

                        if new == True:
                            otdelka = Otdelka.objects.filter(otdelka=item['otdelka']).values('id').get()
                            try:
                                srok = SrokSdachi.objects.filter(srok=item['srok']).values('id').get()
                            except:
                                srok = {'id': 34} # Неизвестно
                            parametr = SellList.objects.filter(idAvito=item['id_avito']).values('idAvito').get()

                            nov = NovostroySellList(parametr_id=parametr['idAvito'], idOtdelka_id=otdelka['id'],
                                                    idSrok_id=srok['id']
                                                    )
                            nov.save()
                    print('Сохранили', (SellList.objects.count() - test))
    return render(request)

def get_page_nubmer(city_url, type):
    url = 'https://www.avito.ru/{}/kvartiry/prodam/{}'
    html = get_html(url.format(str(city_url), str(type)), True)

    try:
        soup = BeautifulSoup(html, 'lxml')
        page = soup.find('div', class_='pagination js-pages').find('div', class_='pagination-pages clearfix').find('a',
                                                                                                                   text='Последняя',
                                                                                                                   class_='pagination-page').get(
            'href')
        page = int(re.sub("\D", "", page))
    except:
        page = 1

    return page


def get_page(city_url, page, types):
    pattern = 'https://www.avito.ru/{}/kvartiry/prodam/{}?p={}'
    url = pattern.format(str(city_url), str(types), str(page))
    html = get_html(url, True)
    if html:
        if len(html) <= 256:
            sleep(7)
            get_page(city_url, page, types)
        else:
            soup = BeautifulSoup(html, 'lxml')
            blocks = soup.find_all('div', {'data-marker': 'item'})

            info = []
            for block in blocks:
                link = block.find('a', {'itemprop': 'url'}).get('href')
                price = block.find('span', {'itemprop': 'price'}).text.strip().replace(' ', '').replace('₽', '')
                # Убераем лишние знаки
                idAvito = re.sub(r'.+?(?=_).', '', link)

                if price != 'Договорная':
                    info.append({
                        'link': link,
                        'price': price,
                        'idAvito': idAvito
                    })
            return info
    else:
        sleep(7)
        get_page(city_url, page, types)



def get_full_page(infoAll):
    pattern = 'https://www.avito.ru/{}'
    global data
    data = []
    for info in infoAll:
        url = pattern.format(str(info['link']))
        html = get_html(url)
        if html != None:
            try:
                data = (get_full_data(html, url))
            except:
                continue
        else:
            continue
    print(len(data))
    return data


def get_full_data(html, url):
    soup = BeautifulSoup(html, 'lxml')
    try:
        name = soup.find('span', class_='title-info-title-text').text
    except:
        name = "Null"

    try:
        t = (soup.find('div', class_='title-info-metadata-item-redesign').text).strip()
        dataAdd = format_date(t)
    except:
        dataAdd = date(2019, 11, 1)

    # Получаем цены
    try:
        allPrices = soup.find('div', {'class': 'price-value-prices-wrapper'}).find_all('li', {'itemprop': 'price'})
    except:
        allPrices = 0

    try:
        fullPriceRUB = int(re.sub("\D", "", allPrices[0].text.strip()))
    except:
        fullPriceRUB = 0

    try:
        fullPriceUSD = int(re.sub("\D", "", allPrices[1].text.strip()))
    except:
        fullPriceUSD = None
    try:
        priceForMetres = int(re.sub("\D", "", allPrices[3].text.strip()))
    except:
        priceForMetres = None
    # Получаем параметры дома

    script_text = soup.find("script").text.split("= ", 1)[1]

    json_data = loads(script_text[:script_text.find(";")])
    try:
        id = int(json_data[0]['dynx_prodid'])
    except:
        id = 'Null'
    try:
        offer_type = json_data[1]['offer_type']  # Тип продажи
    except:
        offer_type = 'Null'
    try:
        if json_data[1]['commission'] == 'Посредник' or soup.find('div',
                                                                  class_='seller-info-value').next_sibling.next_sibling.text == 'Агентство':
            commission = True
        else:
            commission = False
    except:
        commission = False
    try:
        area_kitchen = float(re.sub("[^(0-9.)]", "", json_data[1]['area_kitchen']))  # Размер кухни
    except:
        area_kitchen = None
    try:
        area_live = float(re.sub("[^(0-9.)]", "", json_data[1]['area_live']))  # Жилая зона
    except:
        area_live = None
    try:
        area = float(re.sub("[^(0-9.)]", "", json_data[1]['area']))  # Всего метров
    except:
        area = None
    try:
        rooms = json_data[1]['rooms']  # Комнат
        if rooms == 'Студия' or rooms == 'Своб. планировка':
            room = 6
        elif rooms == '> 9' or int(rooms) > 5:
            room = 7
        else:
            room = int(rooms)
    except:
        room = None
    try:
        type = json_data[1]['commission']  # Вторичка
    except:
        type = 'Null'
    try:
        t = json_data[1]['house_type']  # Тип дома
        house_type = type_house(t)
    except:
        house_type = "Null"
    try:
        floor = int(json_data[1]['floor'])
    except:
        floor = 'Null'
    try:
        floors_count = int(json_data[1]['floors_count'])
    except:
        floors_count = 'Null'

    ##Новостройка
    if json_data[1]['type'] == 'Новостройка':
        try:
            otdelka = (json_data[1]['otdelka']).lower()
        except:
            otdelka = 'Неизвестно'

    try:
        all_li = soup.find_all('li', class_='item-params-list-item')
        li = all_li[-1]
        li = li.contents
        srok = li[2]
        if ((li[1]).contents)[0] == 'Срок сдачи: ':
            if srok == 'сдан ':
                srok = 'сдан'
            else:
                srok = srok.replace(' кв. ', '-')
                srok = srok.replace(' года ', '')
        else:
            srok = 'Неизвестно'
        # srok = (srok.split('-')).lower()
    except:
        srok = 'Неизвестно'

    # Координаты дома
    try:
        adress_lat = float(
            soup.find('div', {'class': 'b-search-map expanded item-map-wrapper js-item-map-wrapper'}).get(
                'data-map-lat'))
        adress_lon = float(
            soup.find('div', {'class': 'b-search-map expanded item-map-wrapper js-item-map-wrapper'}).get(
                'data-map-lon'))
    except:
        adress_lat = 0
        adress_lon = 0

    # Описание
    try:
        description = soup.find('div', {'class': 'item-description-text'}).text.strip()
    except:
        description = soup.find('div', {'class': 'item-description-html'}).text.strip()

    check_ban = soup.find('div', class_='item-view-warning item-view-warning_color-red')

    if not check_ban:
        if json_data[1]['type'] != 'Новостройка':
            data.append({'id_avito': id,
                         'fullPriceRUB': fullPriceRUB,
                         'fullPriceUSD': fullPriceUSD,
                         'priceForMetres': priceForMetres,
                         'agent': commission,
                         'area_kitchen': area_kitchen,
                         'area_live': area_live,
                         'area': area,
                         'room': room,
                         'house_type': house_type,
                         'floor': floor,
                         'total_floor': floors_count,
                         'adress_lat': adress_lat,
                         'adress_lon': adress_lon,
                         'date': dataAdd,
                         'description': description
                         })
        else:
            data.append({'id_avito': id,
                         'fullPriceRUB': fullPriceRUB,
                         'fullPriceUSD': fullPriceUSD,
                         'priceForMetres': priceForMetres,
                         'agent': commission,
                         'area_kitchen': area_kitchen,
                         'area_live': area_live,
                         'area': area,
                         'room': room,
                         'house_type': house_type,
                         'floor': floor,
                         'total_floor': floors_count,
                         'adress_lat': adress_lat,
                         'adress_lon': adress_lon,
                         'date': dataAdd,
                         'srok': srok,
                         'otdelka': otdelka,
                         'description': description

                         })
    return data


def get_html(url, full=False):
    proxys = [{'https': 'https://jr5v5F:JT4T6v@185.128.213.89:8000/'},
              {'https': 'https://jr5v5F:JT4T6v@195.158.225.85:8000/'},
              {'https': 'https://jr5v5F:JT4T6v@185.128.212.159:8000/'}
              # {'https': 'https://aUXGYK:JHZhUS@193.31.102.247:9745/'},
              # {'https': 'https://aUXGYK:JHZhUS@193.31.103.189:9308/'}
              ]
    current_proxy = randint(0, len(proxys) - 1)

    try:
        user_agent = {'User-Agent': generate_user_agent(device_type='desktop', os=('mac', 'linux'))}

        jar = requests.cookies.RequestsCookieJar()
        jar.set('v=1566020312',
                'sx=H4sIAAAAAAACA52RzVLCQAzH32XPHrLd2Ka8TYk2YNoJGDCKw7sbDyhe3Zncdn7%2Fr8%2BCPkl%2F8Tc%2BAjKxiQarC0bZfJa3simHtoNn7xQMlCmMJDAI2FAZgMtDeS6b%2Btj30AN07fpQ2v645ZdufXk%2FO4A7oZOhoN2QUxi2PYvMSQkNBeIgDGfwCLpDNmg9JrKrw%2FwEl8OyLEGSVvIrAhDekHW',
                domain='avito.ru', path='/')
        session = requests.Session()

        # r = session.get(url, allow_redirects=False, headers=user_agent, cookies=jar, proxies=proxys[current_proxy],
        #                 timeout=2)
        r = session.get(url, allow_redirects=False, headers=user_agent, cookies=jar, timeout=2)
        if r.status_code == 200 and (r.text != None):
            sleep(randint(3, 10))
            return r.text
        elif r.status_code == 302:
            print('Получили бан')
            sleep(300)
            if full:
                get_html(url, True)
            else:
                return None
        else:
            print("Причина поломки")
            print(url)
            print(r.status_code)
            sleep(randint(4, 6))
            if full:
                get_html(url, True)
            else:
                return None

    except:
        print("Ошибка таймаута")
        sleep(randint(5, 6))
        if full:
            get_html(url, True)
        else:
            return None


def format_date(time):
    if type(time) == list:
        kvartal = date_kvartal(time[0])
        time = date(time[1], kvartal, 1)


    elif re.search(r'\bсегодня\b', time):
        time = date.today()
    elif re.search(r'\bвчера\b', time):
        time = date.today() - timedelta(days=1)
    else:
        t = re.sub(r'([0-9:])', '', time)
        t = re.sub(r'[\W$]', '', t)
        t = re.sub(r'[\w]$', '', t)
        mounth = int((date_mounth(t)))
        day = re.sub(r'[:]', '', time)
        day = re.sub(r'\b(?:(?!(^[\d]+))\w)+\b', '', day)
        day = int(re.sub(r'[\s]', '', day))
        time = date(2019, mounth, day)
    return time


def date_mounth(x):
    return {
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }.get(x)


def date_kvartal(x):
    return {
        "1": 1,
        "2": 4,
        "3": 7,
        "4": 10,
    }.get(x)


def type_house(x):
    return {
        "Кирпичный": 1,
        "Панельный": 2,
        "Монолитный": 3,
        "Блочный": 4,
        "Деревянный": 5,
    }.get(x)
