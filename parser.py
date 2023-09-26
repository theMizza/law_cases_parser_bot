import requests
from bs4 import BeautifulSoup
from random import choice
from bot_db_connector import *


class Parser:
    UAS = (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17',
        'Mozilla/5.0 (Linux; U; Android 2.2; fr-fr; Desire_A8181 Build/FRF91) App3leWebKit/53.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; FunWebProducts; .NET CLR 1.1.4322; PeoplePal 6.2)',
        'Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
        'Opera/9.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.01',
        'Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 3.5.30729)')

    def parse_data(self, case_id: int):
        case = Cases.get(id=case_id)
        headers = {'User-Agent': choice(self.UAS)}
        response = requests.get(case.url, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")

        case_num = soup.find(class_='casenumber')
        try:
            court_name = soup.find(class_='header__middle').text
        except Exception:
            court_name = "None"
        case_data_table = soup.find('div', id='cont1')
        case_movement_table = soup.find('div', id='cont2')
        case_sides_table = soup.find('div', id='cont3')

        case_data_table_rows = case_data_table.find_all('tr')
        for i in range(1, len(case_data_table_rows)):
            CaseData.create(case=case,
                            name=case_data_table_rows[i].find_all('td')[0].text,
                            value=case_data_table_rows[i].find_all('td')[1].text)
        case.case_num = case_num.text.split('№')[1]
        case.court_name = court_name
        case.save()

        case_movement_table_rows = case_movement_table.find_all('tr')
        for i in range(2, len(case_movement_table_rows)):
            movements = case_movement_table_rows[i].find_all('td')

            CaseMovements.create(
                case=case,
                event_name=movements[0].text,
                date=movements[1].text,
                time=movements[2].text,
                place=movements[3].text,
                result=movements[4].text,
                reason=movements[5].text,
                add_info=movements[6].text,
                place_date=movements[7].text
            )

        case_sides_table_rows = case_sides_table.find_all('tr')
        for j in range(2, len(case_sides_table_rows)):
            sides = case_sides_table_rows[j].find_all('td')

            CaseSides.create(
                case=case,
                side_type=sides[0].text,
                lastname=sides[1].text,
                inn=sides[2].text,
                kpp=sides[3].text,
                ogrn=sides[4].text,
                ogrnip=sides[5].text
            )

        try:
            executive_lists = soup.find('div', id='cont5')
        except Exception:
            executive_lists = None

        if executive_lists is not None:
            executive_lists_rows = executive_lists.find_all('tr')
            for k in range(2, len(executive_lists_rows)):
                exec_lists = executive_lists_rows[k].find_all('td')
                ExecutiveLists.create(
                    case=case,
                    date=exec_lists[0].text,
                    num=exec_lists[1].text,
                    el_num=exec_lists[2].text,
                    status=exec_lists[3].text,
                    person=exec_lists[4].text,
                )

        db.close()

    def update_data(self, case, bot):
        headers = {'User-Agent': choice(self.UAS)}

        response = requests.get(case.url, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")
        case_data_table = soup.find('div', id='cont1')
        case_movement_table = soup.find('div', id='cont2')
        case_sides_table = soup.find('div', id='cont3')
        case_data_table_rows = case_data_table.find_all('tr')
        case_movement_table_rows = case_movement_table.find_all('tr')
        case_sides_table_rows = case_sides_table.find_all('tr')

        user = case.user.user_id
        if len(case.case_data) == len(case_data_table_rows) - 1:
            pass
        else:
            for q in range(1, len(case_data_table_rows)):
                case_data = case_data_table_rows[q].find_all('td')
                new_data, created = CaseData.get_or_create(
                    case=case,
                    name=case_data[0].text,
                    value=case_data[1].text
                )
                if created:
                    data_change_text = f'В деле {case.name} - №{case.case_num} изменения во вкладке Дело\n' \
                                       f'{new_data.name}\n' \
                                       f'{new_data.value}\n\n' \
                                       f'Ссылка на дело: {case.url}'
                    bot.send_message(chat_id=str(user), text=data_change_text)

        if len(case.movements) == len(case_movement_table_rows) - 2:
            pass
        else:
            for i in range(2, len(case_movement_table_rows)):
                movements = case_movement_table_rows[i].find_all('td')

                new_movement, created = CaseMovements.get_or_create(
                    case=case,
                    event_name=movements[0].text,
                    date=movements[1].text,
                    time=movements[2].text,
                    place=movements[3].text,
                    result=movements[4].text,
                    reason=movements[5].text,
                    add_info=movements[6].text,
                    place_date=movements[7].text
                )
                if created:
                    movement_change_text = f'В деле {case.name} - №{case.case_num} изменения во вкладке Движение дела\n' \
                                           f'Наименование события - {new_movement.event_name}\n' \
                                           f'Дата - {new_movement.date}\n' \
                                           f'Время - {new_movement.time}\n' \
                                           f'Место проведения - {new_movement.place}\n' \
                                           f'Результат события - {new_movement.result}\n' \
                                           f'Основание для выбранного результата события - {new_movement.reason}\n' \
                                           f'Основание для выбранного результата события - {new_movement.add_info}\n' \
                                           f'Дата размещения - {new_movement.place_date}\n\n' \
                                           f'Ссылка на дело: {case.url}'
                    bot.send_message(chat_id=str(user), text=movement_change_text)
        if len(case.sides) == len(case_sides_table_rows) - 2:
            pass
        else:
            for j in range(2, len(case_sides_table_rows)):
                sides = case_sides_table_rows[j].find_all('td')

                new_sides, created = CaseSides.get_or_create(
                    case=case,
                    side_type=sides[0].text,
                    lastname=sides[1].text,
                    inn=sides[2].text,
                    kpp=sides[3].text,
                    ogrn=sides[4].text,
                    ogrnip=sides[5].text
                )
                if created:
                    sides_change_text = f'В деле {case.name} - №{case.case_num} изменения во вкладке Стороны по делу\n' \
                                        f'Вид лица, участвующего в деле - {new_sides.side_type}\n' \
                                        f'Фамилия / наименование - {new_sides.lastname}\n' \
                                        f'ИНН - {new_sides.inn}\n' \
                                        f'КПП - {new_sides.kpp}\n' \
                                        f'ОГРН - {new_sides.ogrn}\n' \
                                        f'ОГРНИП - {new_sides.ogrnip}\n\n' \
                                        f'Ссылка на дело: {case.url}'
                    bot.send_message(chat_id=str(user), text=sides_change_text)

        try:
            executive_lists = soup.find('div', id='cont5')
        except Exception:
            executive_lists = None

        if executive_lists is not None:
            executive_lists_rows = executive_lists.find_all('tr')
            if len(case.executive_lists) == len(executive_lists_rows) - 2:
                pass
            else:
                for m in range(2, len(executive_lists_rows)):
                    executives = executive_lists_rows[m].find_all('td')
                    new_executives, created = ExecutiveLists.get_or_create(
                        case=case,
                        date=executives[0].text,
                        num=executives[1].text,
                        el_num=executives[2].text,
                        status=executives[3].text,
                        person=executives[4].text
                    )
                    if created:
                        executives_change_text = f'В деле {case.name} - №{case.case_num} изменения во вкладке Исполнительные листы\n' \
                                                 f'Дата выдачи - {new_executives.date}' \
                                                 f'Серия, номер бланка - {new_executives.num}' \
                                                 f'Номер электронного ИД - {new_executives.el_num}' \
                                                 f'Статус - {new_executives.status}' \
                                                 f'Кому выдан / направлен - {new_executives.person}'
                        bot.send_message(chat_id=str(user), text=executives_change_text)
