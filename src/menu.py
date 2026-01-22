import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import yadisk

from config import (
    DATA_DIRNAME,
    PLOTS_DIRNAME,
    RATES_DIRNAME,
    YADISK_DATA_DIRNAME,
    YADISK_PLOTS_DIRNAME,
    YADISK_RATES_DIRNAME,
    YADISK_TOKEN_PATH,
)
from utils import (
    get_current_date,
    get_dates_between,
    get_rates,
    is_valid_past_date,
    print_rates,
)


def print_menu() -> None:
    print(
        '1. Онлайн-конверсия валют\n'
        '2. Исторические данные за выбранный период\n'
        '3. Построение графика по историческим данным за выбранный период\n'
        '4. Прогноз, исходя из колебаний курса за последние 72 часа\n'
        '5. Сохранение обработанных данных в облачном хранилище Яндекс.Диск\n'
        '6. Выход\n'
    )


def convert_currencies() -> None:
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

    print(f'\n{src_count} {src_currency["name"]} = {dst_count} {dst_currency["name"]}\n')


def historical_data_for_date() -> None:
    date = input('\nИнтересующая Вас дата в формате ДД.ММ.ГГГГ : ')
    print()

    if is_valid_past_date(date):
        print_rates(get_rates(date))
    else:
        print('Некорректная дата')
        return

    print()


def save_plot_by_data() -> None:
    x = []
    y = []

    print()
    print_rates(get_rates(get_current_date()))

    print('\nПостроить график по данным...')

    start = input('От (ДД.ММ.ГГГГ): ')
    if not is_valid_past_date(start):
        print('\nНевалидная дата начала')
        return

    end = input('До (ДД.ММ.ГГГГ): ')
    if not is_valid_past_date(end):
        print('\nНевалидная дата конца')
        return

    currency_code = input('Для (буквенный код валюты): ')

    for date in get_dates_between(start, end):
        rates = get_rates(date)
        currency = next((currency for currency in rates if currency['code'] == currency_code), None)

        if currency is None:
            print('\nКод валюты указан неверно')
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

    print(f'\nГрафик сохранен по пути: "{filepath}"\n')


def currency_forecast() -> None:
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


def save_data_to_yandex_disk() -> None:
    if not os.path.exists(YADISK_TOKEN_PATH):
        print(
            '\nНеобходимо перейти по этой ссылке:'
            '\nhttps://oauth.yandex.ru/authorize?response_type=token&client_id=dee303ce9a9a4693994a1aabaf3a33d7'
            '\nи авторизоваться\n'
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
