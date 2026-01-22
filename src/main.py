import os

from config import (
    PLOTS_DIRNAME,
    RATES_DIRNAME,
)
from menu import (
    convert_currencies,
    currency_forecast,
    historical_data_for_date,
    print_menu,
    save_data_to_yandex_disk,
    save_plot_by_data,
)


def main() -> None:
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
