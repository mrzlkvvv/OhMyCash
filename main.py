from datetime import datetime, timedelta
import os
import csv

from requests import get
from bs4 import BeautifulSoup as BS
import matplotlib.pyplot as plt
import yadisk


CBR_CURRENCY_RATES_URL_TEMPLATE = 'https://cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={}'

DATA_DIRNAME = 'data'
RATES_DIRNAME = os.path.join(DATA_DIRNAME, 'rates')
PLOTS_DIRNAME = os.path.join(DATA_DIRNAME, 'plots')
YADISK_TOKEN_PATH = os.path.join(DATA_DIRNAME, 'yadisk_token.txt')

YADISK_DATA_DIRNAME = '/OhMyCash'
YADISK_RATES_DIRNAME = os.path.join(YADISK_DATA_DIRNAME, 'rates')
YADISK_PLOTS_DIRNAME = os.path.join(YADISK_DATA_DIRNAME, 'plots')


def get_current_date():
    return datetime.now().strftime('%d.%m.%Y')


def save_rates(date):
    filepath = os.path.join(RATES_DIRNAME, f'{date}.csv')

    if os.path.exists(filepath):
        return
    
    response = get(CBR_CURRENCY_RATES_URL_TEMPLATE.format(date)).content
    html = BS(response, 'html.parser')

    date_on_page = html.find('button', class_='datepicker-filter_button').get_text()

    if date_on_page != date:
        print(f'Не нашлось данных за {date}. Будут использованы данные за {date_on_page}\n')
        date = date_on_page
        filepath = os.path.join(RATES_DIRNAME, f'{date_on_page}.csv')

    rates_file = open(filepath, 'w')
    writer = csv.DictWriter(rates_file, fieldnames=('id', 'code', 'count', 'name', 'rate'))
    writer.writeheader()

    for tr in html.find('table').find_all('tr')[1:]:
        tds = tr.find_all('td')

        currency = {
            'id': tds[0].get_text(),
            'code': tds[1].get_text(),
            'count': int(tds[2].get_text()),
            'name': tds[3].get_text(),
            'rate': float(tds[4].get_text().replace(',', '.')),
        }

        writer.writerow(currency)

    writer.writerow({
        'id': '643',
        'code': 'RUB',
        'count': 1,
        'name': 'Российский рубль',
        'rate': 1,
    })

    rates_file.close()
    return filepath


def get_rates(date):
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


def print_rates(rates):
    max_id_len = max(len(currency['id']) for currency in rates) + 4
    max_code_len = max(len(currency['code']) for currency in rates) + 4
    max_count_len = max(len(str(currency['count'])) for currency in rates) + 4
    max_rate_len = max(len(f"{currency['rate']:.4f}") for currency in rates) + 4
    max_name_len = max(len(currency['name']) for currency in rates) + 2

    for currency in rates:
        print(f"| {currency['id'].center(max_id_len)} "
              f"| {currency['code'].center(max_code_len)} "
              f"| {str(currency['count']).center(max_count_len)} "
              f"| {f"{currency['rate']:.4f}".center(max_rate_len)} "
              f"| {currency['name'].center(max_name_len)} |")


def print_menu():
    print(
        '1. Онлайн-конверсия валют\n'
        '2. Исторические данные за выбранный период\n'
        '3. Построение графика по историческим данным за выбранный период\n'
        '4. Прогноз, исходя из колебаний курса за последние 72 часа\n'
        '5. Сохранение обработанных данных в облачном хранилище Яндекс.Диск\n'
        '6. Выход\n'
    )


def convert_currencies():
    rates = get_rates(get_current_date())
    print_rates(rates)

    print('\nВведите буквенный код валюты, которую ...')
    src_currency_code = input('Хотите конвертировать : ')
    dst_currency_code = input('Хотите получить       : ')

    src_currency = next((currency for currency in rates if currency['code'] == src_currency_code), None)
    dst_currency = next((currency for currency in rates if currency['code'] == dst_currency_code), None)
    
    if src_currency is None:
        print('\nКод валюты-источника был указан неверно\n')
        return

    if dst_currency is None:
        print('\nКод целевой валюты был указан неверно\n')
        return

    src_count = float(input('Сколько конвертируем  : '))
    dst_count = round(src_count * src_currency['rate'] / dst_currency['rate'], 4)

    print(f"\n{src_count} {src_currency['name']} = {dst_count} {dst_currency['name']}\n")


def historical_data_for_date():
    date = input('\nИнтересующая Вас дата в формате ДД.ММ.ГГГГ : ')
    print()
    print_rates(get_rates(date))
    print()


def get_dates_between(start, end):
    dates = []
    current_date = datetime.strptime(start, '%d.%m.%Y').date()
    end_date = datetime.strptime(end, '%d.%m.%Y').date()

    while current_date <= end_date:
        dates.append(current_date.strftime('%d.%m.%Y'))
        current_date += timedelta(days=1)

    return dates


def save_plot_by_data():
    x = []
    y = []

    print()
    print_rates(get_rates(get_current_date()))

    print('\nПостроить график по данным...')
    start = input('От (ДД.ММ.ГГГГ): ')
    end = input('До (ДД.ММ.ГГГГ): ')
    currency_code = input('Для (буквенный код валюты): ')

    for date in get_dates_between(start, end):
        rates = get_rates(date)
        currency = next((currency for currency in rates if currency['code'] == currency_code), None)

        if currency is None:
            print('\nКод указан неверно')
            return

        x.append(date)
        y.append(currency['rate'])

    dynamic_width = 6 + (len(x) * 0.2)
    _, ax = plt.subplots(figsize=(dynamic_width, 6))
    ax.plot(x, y, label=f'Курс "{currency_code}"', color='green', marker='o')
    ax.set_xlabel('Дата', fontweight='bold')
    ax.set_ylabel('Курс', fontweight='bold')
    ax.set_title(f'Курс валюты "{currency_code}"', fontweight='bold')
    ax.legend()

    plt.xticks(rotation=90)
    plt.tight_layout()

    filepath = os.path.join(PLOTS_DIRNAME, f'{currency_code}_from_{start}_to_{end}.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')

    print(f'\nФайл сохранен по пути: "{filepath}"\n')


def currency_forecast():
    today = get_current_date()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%d.%m.%Y')

    rates_today = get_rates(today)
    rates_yesterday = get_rates(yesterday)
    rates_2_days_ago = get_rates(two_days_ago)

    print_rates(rates_today)

    currency_code = input('\nБуквенный код валюты: ')

    rate_today = next((c for c in rates_today if c['code'] == currency_code), None)
    rate_yesterday = next((c for c in rates_yesterday if c['code'] == currency_code), None)
    rate_2_days_ago = next((c for c in rates_2_days_ago if c['code'] == currency_code), None)

    if (rate_2_days_ago is None) or (rate_yesterday is None) or (rate_today is None):
        print('Код указан неверно\n')
        return

    forecast = round((rate_2_days_ago['rate'] + rate_yesterday['rate'] + rate_today['rate']) / 3, 5)
    print(f'Прогноз методом простого скользящего среднего на завтра: {forecast}\n')


def save_data_to_yandex_disk():
    if not os.path.exists(YADISK_TOKEN_PATH):
        print(
            '\nНеобходимо перейти по этой ссылке: https://yandex.ru/dev/disk/poligon\n'
            'и кликнуть на кнопку "Получить OAuth-токен"'
        )

        token = input('Затем вставьте токен: ')

        yadisk_token_file = open(YADISK_TOKEN_PATH, 'w')
        yadisk_token_file.write(token)
        yadisk_token_file.close()

        print(f'Токен был сохранен по пути {YADISK_TOKEN_PATH}')

    yadisk_token_file = open(YADISK_TOKEN_PATH, 'r')
    yadisk_token = yadisk_token_file.read()
    yadisk_token_file.close()

    client = yadisk.Client(token=yadisk_token)

    print('\nПроверка токена...')
    if client.check_token():
        print('Токен валидный. Начинаю сохранение данных на диск...')
    else:
        print('Токен невалиден. Запустите сохранение еще раз\n')
        os.remove(YADISK_TOKEN_PATH)
        return

    if not client.exists(YADISK_DATA_DIRNAME):
        client.mkdir(YADISK_DATA_DIRNAME)
    
    for local_dir, _, files in os.walk(DATA_DIRNAME):
        for file in files:
            yadisk_dir = ''

            if local_dir == RATES_DIRNAME:
                yadisk_dir = YADISK_RATES_DIRNAME
            elif local_dir == PLOTS_DIRNAME:
                yadisk_dir = YADISK_PLOTS_DIRNAME
            else:
                yadisk_dir = YADISK_DATA_DIRNAME

            if not client.exists(yadisk_dir):
                client.mkdir(yadisk_dir)

            local_path = os.path.join(local_dir, file)
            yadisk_path = os.path.join(yadisk_dir, file)

            if client.exists(yadisk_path):
                continue

            client.upload(local_path, yadisk_path)
            print(f'Файл "{local_path}" был загружен в "{yadisk_path}"')

    print('\nВсе файлы были загружены\n')


def main():
    os.makedirs(RATES_DIRNAME, exist_ok=True)
    os.makedirs(PLOTS_DIRNAME, exist_ok=True)

    op = ''

    while True:
        print_menu()
        op = input('Ваш запрос: ')

        if op == '1':
            convert_currencies()

        elif op == '2':
            historical_data_for_date()

        elif op == '3':
            save_plot_by_data()

        elif op == '4':
            currency_forecast()

        elif op == '5':
            save_data_to_yandex_disk()

        elif op == '6':
            exit()

        else:
            print('\nНекорректный запрос\n')


if __name__ == '__main__':
    main()
