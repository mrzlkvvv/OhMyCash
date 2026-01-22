import csv
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from bs4 import BeautifulSoup as BS
from requests import get

from config import RATES_DIRNAME

CBR_CURRENCY_RATES_URL_TEMPLATE = 'https://cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={}'


def get_current_date() -> str:
    return datetime.now().strftime('%d.%m.%Y')


def is_valid_past_date(date_str: str) -> bool:
    try:
        date = datetime.strptime(date_str, '%d.%m.%Y')
        return date <= datetime.today()
    except ValueError:
        return False


def save_rates(date: str) -> str:
    filepath = os.path.join(RATES_DIRNAME, f'{date}.csv')
    if os.path.exists(filepath):
        return filepath

    response = get(CBR_CURRENCY_RATES_URL_TEMPLATE.format(date)).content
    html = BS(response, 'html.parser')

    btn_with_date = html.find('button', class_='datepicker-filter_button')
    if btn_with_date is None:
        print('Не удалось найти дату на странице с курсами валют')
        exit(-1)

    date_on_page = btn_with_date.get_text()

    if date_on_page != date:
        print(f'Не нашлось данных за {date}. Будут использованы данные за {date_on_page}\n')

        date = date_on_page

        filepath = os.path.join(RATES_DIRNAME, f'{date_on_page}.csv')
        if os.path.exists(filepath):
            return filepath

    rates_file = open(filepath, 'w')
    writer = csv.DictWriter(rates_file, fieldnames=('id', 'code', 'count', 'name', 'rate'))
    writer.writeheader()

    table = html.find('table')
    if table is None:
        print('Не удалось найти таблицу на странице с курсами валют')
        exit(-1)

    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')

        currency = {
            'id': tds[0].get_text(),
            'code': tds[1].get_text(),
            'count': int(tds[2].get_text()),
            'name': tds[3].get_text(),
            'rate': float(tds[4].get_text().replace(',', '.')),
        }

        writer.writerow(currency)  # type: ignore[arg-type]

    writer.writerow(
        {
            'id': '643',
            'code': 'RUB',
            'count': 1,
            'name': 'Российский рубль',
            'rate': 1,
        }
    )

    rates_file.close()
    return filepath


def get_rates(date: str) -> List[Dict[str, Any]]:
    filepath = os.path.join(RATES_DIRNAME, f'{date}.csv')

    if not os.path.exists(filepath):
        filepath = save_rates(date)

    currencies = []

    with open(filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            currency = {
                'id': row['id'],
                'code': row['code'],
                'count': int(row['count']),
                'name': row['name'],
                'rate': float(row['rate']),
            }
            currencies.append(currency)

    return currencies


def print_rates(rates: List[Dict[str, Any]]):
    max_id_len = max(len(currency['id']) for currency in rates) + 4
    max_code_len = max(len(currency['code']) for currency in rates) + 4
    max_count_len = max(len(str(currency['count'])) for currency in rates) + 4
    max_rate_len = max(len(f'{currency["rate"]:.4f}') for currency in rates) + 4
    max_name_len = max(len(currency['name']) for currency in rates) + 2

    for currency in rates:
        print(
            f'| {currency["id"].center(max_id_len)} '
            f'| {currency["code"].center(max_code_len)} '
            f'| {str(currency["count"]).center(max_count_len)} '
            f'| {f"{currency['rate']:.4f}".center(max_rate_len)} '
            f'| {currency["name"].center(max_name_len)} |'
        )


def get_dates_between(start, end) -> List[str]:
    dates = []

    current_date = datetime.strptime(start, '%d.%m.%Y').date()
    end_date = datetime.strptime(end, '%d.%m.%Y').date()

    while current_date <= end_date:
        dates.append(current_date.strftime('%d.%m.%Y'))
        current_date += timedelta(days=1)

    return dates
