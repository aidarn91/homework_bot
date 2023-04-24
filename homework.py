import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

import exceptions

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HEADERS = {'Authorization': f'OAuth { PRACTICUM_TOKEN }'}
MISSING_ENV_VAR = 'Отсутствует переменная окружения - {}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    logging.info('Проверка наличия всех токенов')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    logging.debug("Процесс отправки сообщения (функция send_message)")
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(
            f'Сообщение в Telegram отправлено: {message}'
        )
    except telegram.TelegramError as telegram_error:
        logging.error(
            f'Сообщение в Telegram не отправлено: {telegram_error}'
        )
        raise exceptions.SendMessageException(
            f'Cбой при отправке сообщения в Telegram: {message}.'
        )


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != 200:
            code_api_msg = (
                f'Эндпоинт {ENDPOINT} недоступен.'
                f' Код ответа API: {response.status_code}'
            )
            logging.error(code_api_msg)
            raise exceptions.TheAnswerIsNot200Error(code_api_msg)
        return response.json()
    except requests.exceptions.RequestException as request_error:
        code_api_msg = f'Код ответа API (RequestException): {request_error}'
        logging.error(code_api_msg)
        raise exceptions.RequestExceptionError(code_api_msg) from request_error
    except Exception as error:
        code_api_msg = f'Ошибка преобразования к формату json: {error}'
        logging.error(code_api_msg)
        raise exceptions.GetAPIAnswerException(code_api_msg) from error


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('Ошибка, homeworks не является словарем')
        raise TypeError('Ошибка, homeworks не является словарем')
    if not isinstance(response.get('homeworks'), list):
        logging.error('Ошибка, homeworks не является списком')
        raise TypeError('Ошибка, homeworks не является списком')
    try:
        list_works = response['homeworks']
    except KeyError:
        logging.error('Ошибка словаря по ключу homeworks')
        raise KeyError('Ошибка словаря по ключу homeworks')
    try:
        homework = list_works[0]
    except IndexError:
        logging.error('Список домашних работ пуст')
        raise IndexError('Список домашних работ пуст')
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус работы."""
    logging.info('Проводим проверки и извлекаем статус работы')
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name в ответе API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    return ('Изменился статус проверки работы "{homework_name}". {verdict}'
            ).format(
                homework_name=homework_name,
                verdict=HOMEWORK_VERDICTS[homework_status]
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутсвуют переменные окружения')
        raise ValueError('Проверьте переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            timestamp = response.get('current_date', timestamp)
        except exceptions.SendMessageError:
            pass
        except Exception:
            send_message(bot, message)
            logging.critical(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
