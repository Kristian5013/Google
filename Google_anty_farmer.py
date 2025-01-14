from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
import logging
import re
import asyncio
import time
import random
import string
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException , WebDriverException
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from multiprocessing import Process
from multiprocessing import Process, Manager
import SMSAPI
import requests
import pygetwindow
import sys
import subprocess
import os
import aiohttp
import tempfile
import shutil
import json
from queue import Queue, Empty
from SMSAPI import (
    check_available_numbers,
    get_phone_number,
    get_sms_code,
    complete_activation,
    cancel_activation,
    get_status,
    sync_get_request
)





# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Введите ваш api_id и api_hash
api_id = '26282201'
api_hash = '287f39dd085b9c050cc3c05bc264b3c4'
bot_username = '@GmailFarmerBot'
API_KEY = '143095U681e26c0b02080043aa6c22e85ae6d10'

# Создаем клиента
client = TelegramClient('session_name', api_id, api_hash)


# Глобальная переменная для хранения текущего ID профиля
current_profile_id = None
response = None

# Глобальный словарь для отслеживания запросов
requests_status = {}


# Конфигурация API Dolphin Anty
API_URL = 'http://localhost:3001/v1.0'
API_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiMWU4MDllYjhhYzM3YTExYzlmMGM5NTI2ZmQ3NGZjYzI1OGUxMzFjZDI0ZDRiNjg2ZDEyOTZjMDY1YTAxN2MwODllNDY1MzdjYjQ5NWMwNTEiLCJpYXQiOjE3MzYzMDY0OTUuMjA0OTIyLCJuYmYiOjE3MzYzMDY0OTUuMjA0OTIzLCJleHAiOjE3Mzg4OTg0OTUuMTkyNDgxLCJzdWIiOiIzNjkzMjM2Iiwic2NvcGVzIjpbXX0.QIzjQWYjXfQbCFq1SgFrkNGirHxVmfdvgbKT3uSBbQctR02zF3o7cNpB_wWag86V4ABdUQCTdu6GzdA6c9tgmFc1RmWbzBrpcmREOf5fVpRL42gDqoZgrIh4EPrbLzBCjFdqiQDRpd5gFqKRMDZG9OqbSuFbqD6hOsXMhXQzwc68daJtiL_ufSAuqtgWwqbg_CCzVHM9VsgCjH_S1-6H6_psgOFdHsK703CUR3ObWeC0sKJhRsuT_KihdG4BnPj3o7hZcNCA5z-ASGUhngzghyW45yxnHx1nhF-z7TGhxSh1mbHGrKYq0KzKeyx0_dmCMQhUsAShj2XKoCTrm6GgqA3jr4qDHJ_rxLRIGTLkmkE4FmwZ2S7InO3KffcAVCIOUXEU1FERmObABPqvK7dx9WbEEL3H8T7G3xxSBqeqSgccA7pL-8z4V_e2bXFMdBnHBCXoaL0FyE2MiR5SVfph4h33v-MlL7bdHUF9rVJr2dOuR9yIWQB5JhI24WQeibl10ptLa8ZwACzT8gBM6UkOi2yBvhFkRR7kmaPeRphJmXA8CSsLfgneUYAFsrgyHJKKXTMGUF-wxI1oirS_2VlWjI57tjcaLDMavb5zeJS9y9f3vLyomA-igarIaIqCU0yiR4mmI1NEfikTysYPllCQIDAR-CaxOp-jw0IfmOBijBk'
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}


def restart_script():
    """Функция для перезапуска текущего скрипта."""
    logger.info("Перезапуск процесса с самого начала...")
    try:
        time.sleep(10)  # Небольшая пауза перед перезапуском
        subprocess.Popen([sys.executable, sys.argv[0]])  # Запуск нового процесса
        sys.exit(0)  # Завершение текущего процесса
    except Exception as e:
        logger.error(f"Ошибка при перезапуске скрипта: {e}")
        raise


async def stop_profile(profile_id):
    """
    Асинхронная функция для остановки профиля через Dolphin Anty API.
    """
    stop_url = f"{API_URL}/browser_profiles/{profile_id}/stop?update_fingerprint=1"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(stop_url, headers=HEADERS) as response:
                if response.status == 200:
                    logger.info(f"Профиль {profile_id} успешно остановлен.")
                else:
                    logger.error(f"Ошибка при остановке профиля {profile_id}: {response.status} - {await response.text()}")
        except Exception as e:
            logger.error(f"Ошибка при остановке профиля {profile_id}: {e}")


def handle_activation_error(profile_id, api_url, headers, API_KEY, activation_id):
    """Обработка ошибки активации."""
    logger.error("Ошибка в процессе активации. Выполняется отмена активации...")
    cancel_activation(API_KEY, activation_id)
    stop_profile(profile_id, api_url, headers)
    restart_script()


def wait_for_page_load(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("Страница полностью загружена.")
    except TimeoutException:
        print("Ошибка: Страница не загрузилась в течение установленного времени. Перезапуск...")
        handle_activation_error(driver, API_KEY)


# Функция генерации логина
def generate_username(first_name, last_name):
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{first_name}{last_name}{suffix}"


# Генерация имени и фамилии
nicknames = ["Adalyn", "Balthazar", "Cressida","Alexander", "Sophia", "Ethan", "Olivia", "Liam", "Isabella", "Noah", "Emma", 
    "James", "Ava", "Benjamin", "Mia", "Logan", "Charlotte", "Lucas", "Amelia", 
    "Mason", "Harper", "Elijah", "Evelyn", "Oliver", "Abigail", "Aiden", "Ella", 
    "Jackson", "Elizabeth", "Sebastian", "Sofia", "Henry", "Emily", "Matthew", 
    "Avery", "Owen", "Scarlett", "Wyatt", "Lily", "Jack", "Aria", "Daniel", "Grace", 
    "Carter", "Chloe", "Gabriel", "Ellie", "Luke", "Layla", "Isaac", "Zoey", 
    "Jayden", "Hannah", "Samuel", "Nora", "Grayson", "Lillian", "Dylan", "Addison", 
    "Levi", "Aubrey", "Lincoln", "Eleanor", "Isaiah", "Natalie", "Caleb", "Luna", 
    "Ryan", "Savannah", "Nathan", "Brooklyn", "Hunter", "Bella", "Christian", 
    "Claire", "Aaron", "Aurora", "Joshua", "Penelope", "Andrew", "Violet", 
    "Joseph", "Hazel", "Thomas", "Victoria", "Eli", "Lucy", "David", "Riley", 
    "Adam", "Stella", "Asher", "Zoe", "Jonathan", "Leah", "Connor", "Audrey", 
    "Jeremiah", "Allison", "Hudson", "Maya", "Nolan", "Sarah", "Easton", "Ariana"]

last_names = ["Ainsworth", "Brewster", "Cavendish","Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", 
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", 
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", 
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", 
    "Mitchell", "Carter", "Roberts", "Gomez"]

first_name = random.choice(nicknames)
last_name = random.choice(last_names)
username = generate_username(first_name, last_name)


def generate_random_name():
    first_name = random.choice(nicknames)
    last_name = random.choice(last_names)
    return first_name, last_name


driver = None
sms_driver = None


async def extract_email_password(message):
    """
    Извлекает email и пароль из сообщения Telegram.
    """
    email_pattern = r"Email:\s*(\S+)"
    password_pattern = r"Пароль:\s*(\S+)"
    email_match = re.search(email_pattern, message)
    password_match = re.search(password_pattern, message)
    if email_match and password_match:
        email = email_match.group(1).replace("@gmail.com", "")
        password = password_match.group(1)
        return email, password
    return None, None

async def send_registration_command():
    """
    Отправляет команду регистрации нового Gmail боту.
    """
    try:
        if not client.is_connected():
            logger.info("Telegram клиент не подключён. Подключаем...")
            await client.start()
            logger.info("Telegram клиент успешно подключён.")
        
        await client.send_message(bot_username, "\u2795 Зарегистрировать новый Gmail")
        logger.info("Команда отправлена: '➕ Зарегистрировать новый Gmail'.")
    except Exception as e:
        logger.error(f"Ошибка при отправке команды боту: {e}")

async def handle_telegram_responses(profile_id):
    """
    Обрабатывает сообщения Telegram для конкретного профиля.
    """
    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        message_text = event.message.message
        logger.info(f"Получено сообщение от бота: {message_text}")
        
        email, password = await extract_email_password(message_text)
        if email and password:
            requests_status[profile_id] = (email, password)
            logger.info(f"Полученные данные для профиля {profile_id}: Email: {email}, Пароль: {password}")
            await client.disconnect()
        else:
            logger.warning("Не удалось извлечь email или пароль из сообщения.")

    try:
        logger.info(f"Подключаемся к Telegram для профиля {profile_id}...")
        await client.start()
        logger.info("Telegram клиент успешно подключён, ожидаем ответ...")
        await asyncio.sleep(10)  # Ожидание ответа
    except Exception as e:
        logger.error(f"Ошибка в Telegram обработчике для профиля {profile_id}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()

async def get_email_password_from_telegram(profile_id):
    """
    Отправляет запрос и получает email и пароль через Telegram.
    """
    try:
        await send_registration_command()
        await handle_telegram_responses(profile_id)
        
        email, password = requests_status.get(profile_id, (None, None))
        if not email or not password:
            logger.error(f"Не удалось получить данные для профиля {profile_id}.")
            return None, None
        return email, password
    except Exception as e:
        logger.error(f"Ошибка при получении данных от Telegram для профиля {profile_id}: {e}")
        return None, None


# Функция для обработки кнопки "Готово"
async def click_done_button(event):
    """
    Ищет и нажимает кнопку 'Готово' в сообщении Telegram.
    """
    try:
        if event.message.buttons:
            for row_index, row in enumerate(event.message.buttons):
                for col_index, button in enumerate(row):
                    logger.info(f"Обнаружена кнопка: {button.text}")
                    if 'готово' in button.text.lower():
                        await event.message.click(row_index * len(row) + col_index)
                        logger.info("Кнопка 'Готово' была нажата.")
                        return
        logger.warning("Кнопка 'Готово' не найдена.")
    except Exception as e:
        logger.error(f"Ошибка при нажатии кнопки 'Готово': {e}")

# Функция для активации холда
async def activate_hold(profile_id):
    """
    Находит сообщение с данными профиля и нажимает кнопку 'Готово'.
    """
    try:
        if not client.is_connected():
            logger.info("Подключение Telegram клиента для обработки кнопки 'Готово'...")
            await client.start()

        @client.on(events.NewMessage(from_users=bot_username))
        async def handle_new_message(event):
            # Проверяем, связано ли сообщение с профилем
            if str(profile_id) in event.message.text:
                logger.info(f"Сообщение связано с профилем {profile_id}. Проверяем наличие кнопки 'Готово'.")
                await click_done_button(event)
            else:
                logger.info(f"Сообщение не связано с профилем {profile_id}. Пропуск.")

        # Задержка для ожидания сообщений
        await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки 'Готово' для профиля {profile_id}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()



async def start_browser_with_number(profile_id, phone_number, activation_id, email, password, first_name, last_name, sms_api_key, api_url, headers):
    """
    Запускает браузер с привязкой к указанному порту и выполняет регистрацию, используя номер телефона.
    """

    # Запуск профиля
    start_profile_url = f'{api_url}/browser_profiles/{profile_id}/start?automation=1'
    response = requests.get(start_profile_url, headers=headers)

    if response.status_code == 200:
        start_data = response.json()
        port = start_data['automation']['port']
        print(f"Профиль {profile_id} запущен. Порт: {port}")
        
        # Настройка Selenium для работы с профилем
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{port}")
        chrome_options.add_argument("--disk-cache-size=0")

        driver = None

        # Настройк ожидания
        wait = WebDriverWait(driver, 20)
        sleep = 7

        try:
            # Подключение к профилю Dolphin Anty
            driver = webdriver.Chrome(options=chrome_options)
            driver.maximize_window()
            wait = WebDriverWait(driver, 20)
            time.sleep(sleep)


            # Переход на страницу регистрации Google
            driver.get("https://accounts.google.com/signup")
            wait = WebDriverWait(driver, 20)


            # Ввод имени, фамилии и нажатие кнопки "Далее"
            try:
                wait_for_page_load(driver)
                # Ожидание и ввод имени
                first_name_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "firstName"))
                )
                first_name_field.send_keys(first_name)
                print("Поле 'Имя' найдено и заполнено.")

                # Ожидание и ввод фамилии
                last_name_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "lastName"))
                )
                last_name_field.send_keys(last_name)
                print("Поле 'Фамилия' найдено и заполнено.")
                time.sleep(sleep)

                # Ожидание и нажатие кнопки "Далее"
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[jsname='V67aGc']"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                print("Кнопка 'Далее' найдена и нажата.")
                time.sleep(sleep)

            except TimeoutException:
                print("Ошибка: Не удалось найти поля 'Имя', 'Фамилия' или кнопку 'Далее'. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, sms_api_key, activation_id)
            except Exception as e:
                print(f"Произошла ошибка: {e}. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, sms_api_key, activation_id)

            try:
                wait_for_page_load(driver)
                # Генерация случайных значений
                day = random.randint(1, 30)
                year = random.randint(1990, 2006)
                random_month_value = random.randint(1, 12)

                # Ожидание и ввод дня
                day_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "day"))
                )
                day_field.send_keys(str(day))
                print(f"Поле 'День' найдено и заполнено: {day}")

                # Ожидание и ввод года
                year_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "year"))
                )
                year_field.send_keys(str(year))
                print(f"Поле 'Год' найдено и заполнено: {year}")

                # Установка месяца через JavaScript
                driver.execute_script("document.getElementById('month').value = arguments[0];", random_month_value)
                print(f"Месяц установлен: {random_month_value}")

                # Установка пола через JavaScript (мужской)
                driver.execute_script("document.getElementById('gender').value = '1';")
                print("Пол установлен: Мужской")
                time.sleep(sleep)

                # Нажатие кнопки "Далее"
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[jsname='V67aGc']"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                print("Кнопка 'Далее' успешно нажата.")
                time.sleep(sleep)

            except TimeoutException:
                print("Ошибка: Не удалось найти элементы для ввода даты рождения, выбора пола или кнопки 'Далее'. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)

            except Exception as e:
                print(f"Произошла ошибка: {e}. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)


            # Проверка кнопки "Create your own Gmail address", ввод email и нажатие "Далее"
            try:
                wait_for_page_load(driver)
                # Проверка наличия кнопки "Create your own Gmail address" и нажатие
                try:
                    create_own_address_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Create your own Gmail address')]"))
                    )
                    create_own_address_button.click()
                    print("Нажата кнопка 'Create your own Gmail address'.")
                except TimeoutException:
                    print("Кнопка 'Create your own Gmail address' отсутствует. Продолжаем выполнение.")

                # Ожидание и ввод email
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "input"))
                )
                email_field.send_keys(email)
                print(f"Email введён: {email}")
                time.sleep(sleep)

                # Ожидание кнопки "Далее" и её нажатие
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[jsname='LgbsSe']"))
                )
                next_button.click()
                print("Кнопка 'Далее' успешно нажата.")
                time.sleep(sleep)
                
            except TimeoutException:
                print("Ошибка: Не удалось выполнить один из шагов (проверка кнопки, ввод email или нажатие 'Далее'). Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)

            except Exception as e:
                print(f"Произошла ошибка: {e}. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)


            # Ввод пароля
            try:
                wait_for_page_load(driver)
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "Passwd"))
                )
                driver.execute_script("arguments[0].value = arguments[1];", password_field, password)
                print("Пароль успешно введён через JavaScript.")

                # Ожидание и ввод подтверждения пароля
                confirm_password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "PasswdAgain"))
                )
                driver.execute_script("arguments[0].value = arguments[1];", confirm_password_field, password)
                print("Подтверждение пароля успешно введено через JavaScript.")

                # Имитация события 'input' и 'change' для обоих полей
                for field in [password_field, confirm_password_field]:
                    driver.execute_script("""
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """, field)

                # Небольшая пауза для стабильности
                time.sleep(sleep)

                # Ожидание кликабельности и нажатие кнопки "Далее"
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[jsname='LgbsSe']"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                print("Кнопка 'Далее' успешно нажата после ввода пароля.")
                time.sleep(sleep)
            except TimeoutException:
                print("Ошибка: Поля для ввода пароля или кнопка 'Далее' не загрузились. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
            except Exception as e:
                print(f"Произошла ошибка при вводе пароля или нажатии кнопки 'Далее': {e}. Перезапуск...")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)


            delay = 10
            max_wait_time = 60

            try:
                wait_for_page_load(driver)
                # Шаг 1: Ввод номера телефона
                logger.info("Начинаем ввод номера телефона.")
                phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "phoneNumberId"))
                )
                driver.execute_script("arguments[0].value = arguments[1];", phone_input, phone_number)
                logger.info("Номер телефона введён.")
                time.sleep(sleep)

                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[jsname='LgbsSe']"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                logger.info("Кнопка 'Next' нажата.")

                # Шаг 2: Ожидание получения кода подтверждения
                logger.info("Ожидание получения кода подтверждения в течение 40 секунд...")
                try:
                    wait_for_page_load(driver)
                    code = None
                    for attempt in range(8):  # 8 попыток с интервалом в 5 секунд (всего 40 секунд)
                        # Запрос статуса через SMS-Activate API
                        url = f"https://api.sms-activate.ae/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={activation_id}"
                        response = requests.get(url)
                        if response.status_code == 200:
                            logger.info(f"Ответ API (попытка {attempt + 1}): {response.text}")
                            
                            if "STATUS_OK" in response.text:  # Код подтверждения получен
                                code = response.text.split(":")[1]
                                logger.info(f"Код подтверждения получен: {code}")
                                break
                            elif "STATUS_WAIT_CODE" in response.text:  # Код ещё не готов
                                logger.info("Код ещё не готов. Ожидаем...")
                                time.sleep(5)
                            else:  # Неожиданный статус
                                logger.error(f"Неожиданный статус API: {response.text}")
                                raise Exception("API вернул неожиданный статус.")
                        else:
                            logger.error(f"Ошибка при запросе статуса: {response.text}")
                            raise Exception("Ошибка при запросе статуса.")
                    
                    if not code:  # Если код не был получен за отведённое время
                        logger.error("Код подтверждения не был получен в установленное время.")
                        handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
                        return
                except Exception as e:
                    logger.error(f"Ошибка в процессе ожидания кода подтверждения: {e}")
                    handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
                    return

                # Шаг 3: Ввод кода подтверждения
                logger.info("Вводим код подтверждения.")
                try:
                    wait_for_page_load(driver)
                    confirmation_code_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "code"))
                    )
                    if confirmation_code_input.is_displayed() and confirmation_code_input.is_enabled():
                        driver.execute_script("arguments[0].value = arguments[1];", confirmation_code_input, code)
                        logger.info("Код подтверждения введён.")
                        time.sleep(2)

                        # Нажимаем кнопку "Next"
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[jsname='LgbsSe']"))
                        )
                        driver.execute_script("arguments[0].click();", next_button)
                        logger.info("Код подтверждения отправлен.")
                    else:
                        logger.error("Поле для ввода кода подтверждения неактивно или недоступно.")
                        raise Exception("Поле ввода кода недоступно.")
                except TimeoutException:
                    logger.error("Поле ввода кода подтверждения не появилось.")
                    logger.info("HTML страницы для диагностики:")
                    logger.info(driver.page_source)
                    handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
                    return
                except Exception as e:
                    logger.error(f"Ошибка при вводе кода подтверждения: {e}")
                    handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
                    return

                # Шаг 4: Завершение активации
                logger.info("Завершаем активацию.")
                url = f"https://api.sms-activate.ae/stubs/handler_api.php?api_key={API_KEY}&action=setStatus&status=6&id={activation_id}"
                response = requests.get(url)
                if response.status_code == 200 and "ACCESS_ACTIVATION" in response.text:
                    logger.info("Личность подтверждена успешно.")
                else:
                    logger.error(f"Ошибка завершения активации: {response.text}")
            except Exception as e:
                logger.error(f"Произошла ошибка: {e}")  
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)



            try:
                wait_for_page_load(driver)
                # Ожидание полной загрузки страницы
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                print("Страница полностью загружена.")

                # Ожидание появления кнопки `Skip`
                skip_button = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "recoverySkip"))
                )
                print("Кнопка 'Skip' найдена.")

                # Прокрутка к кнопке для гарантированной доступности
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", skip_button)
                time.sleep(1)  # Небольшая пауза для стабилизации

                # Проверка кликабельности кнопки
                skip_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "recoverySkip"))
                )

                # Выполнение клика с использованием JavaScript
                driver.execute_script("arguments[0].click();", skip_button)
                print("Кнопка 'Skip' успешно нажата.")

                # Небольшая пауза для стабильности
                time.sleep(sleep)

            except TimeoutException:
                print("Кнопка 'Skip' не найдена или не кликабельна в течение 10 секунд.")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
            except Exception as e:
                print(f"Произошла ошибка при работе с кнопкой 'Skip': {e}")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
                


            try:
                wait_for_page_load(driver)
                # Ожидание полной загрузки страницы
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                print("Страница полностью загружена.")

                # Ожидание появления кнопки `Next`
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[jsname="LgbsSe"]'))
                )
                print("Кнопка 'Next' найдена.")

                # Прокрутка к кнопке для гарантированной доступности
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                time.sleep(1)  # Небольшая пауза для стабилизации

                # Проверка кликабельности кнопки
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[jsname="LgbsSe"]'))
                )

                # Выполнение клика с использованием JavaScript
                driver.execute_script("arguments[0].click();", next_button)
                print("Кнопка 'Next' успешно нажата.")

                # Небольшая пауза для стабильности
                time.sleep(sleep)

            except TimeoutException:
                print("Кнопка 'Next' не найдена или не кликабельна в течение 10 секунд.")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)
            except Exception as e:
                print(f"Произошла ошибка при работе с кнопкой 'Next': {e}")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)



            try:
                wait_for_page_load(driver)
                # Прокрутка страницы вниз, чтобы кнопки стали видимыми
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Ждём, пока элементы кнопок с указанным классом станут доступны
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button.VfPpkd-LgbsSe'))
                )

                # Поиск всех кнопок с одинаковым классом
                buttons = driver.execute_script("""
                    return Array.from(document.querySelectorAll('button.VfPpkd-LgbsSe'));
                """)

                # Убедимся, что найдено как минимум две кнопки
                if len(buttons) < 2:
                    raise Exception("Недостаточно кнопок с указанным классом. Возможно, структура страницы изменилась.")

                # Выбираем вторую кнопку
                target_button = buttons[1]

                # Прокрутка к кнопке для её видимости
                driver.execute_script("""
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, target_button)
                time.sleep(1)

                # Убеждаемся, что кнопка кликабельна
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.VfPpkd-LgbsSe'))
                )

                # Выполнение клика через JavaScript
                driver.execute_script("""
                    arguments[0].click();
                """, target_button)
                time.sleep(sleep)

                print("Вторая кнопка ('I Agree') успешно нажата.")

                # ожидание страницы/оптимизация
                time.sleep(20)

            except TimeoutException:
                print("Кнопка 'I Agree' не найдена или не кликабельна в течение времени ожидания.")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)

            except Exception as e:
                print(f"Произошла ошибка при работе с кнопкой: {e}")
                handle_activation_error(driver, profile_id, api_url, API_KEY, activation_id)


        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
        finally:
            try:
                # Настройка параметров для остановки профиля
                api_url = "https://dolphin-anty-api.com"
                headers = {
                    "Authorization": "Bearer YOUR_API_TOKEN",
                    "Content-Type": "application/json"
                }

                # Проверка наличия необходимых параметров
                if profile_id and api_url and headers:
                    logger.info(f"Остановка профиля {profile_id}...")


                    # Остановка профиля
                    stop_profile(profile_id, api_url, headers)
                    logger.info(f"Профиль {profile_id} успешно остановлен.")

                    # Подтверждение активации
                    complete_activation(api_key=API_KEY, activation_id=activation_id)
                    logger.info(f"Активация с ID {activation_id} успешно завершена.")
                else:
                    logger.error("Не удалось выполнить остановку профиля: отсутствуют необходимые параметры.")
            except Exception as stop_profile_error:
                logger.error(f"Произошла ошибка при остановке профиля: {stop_profile_error}")
            finally:
                logger.info("Завершение всех действий завершено корректно.")





async def start_browser_with_number(profile_id, phone_number, activation_id, email, password, first_name, last_name):
    """
    Имитация регистрации аккаунта с использованием браузера и номера телефона.
    """
    logger.info(f"Запуск браузера для профиля {profile_id}.")
    await asyncio.sleep(5)  # Имитация работы
    logger.info(f"Регистрация завершена для профиля {profile_id}.")

# Основной процесс регистрации
async def process_registration_async(profile_id, API_KEY):
    """
    Основная асинхронная функция для регистрации профиля.
    """
    activation_id = None
    try:
        logger.info(f"Начало процесса для профиля {profile_id}.")

        # Получение номера телефона
        result = get_phone_number(api_key=API_KEY)
        if not result:
            logger.error(f"Не удалось получить номер телефона для профиля {profile_id}.")
            return

        activation_id, phone_number = result
        logger.info(f"Номер телефона: {phone_number} (ID активации: {activation_id})")

        # Имитируем процесс регистрации через браузер
        await asyncio.sleep(5)  # Задержка для имитации
        logger.info(f"Регистрация завершена для профиля {profile_id}.")

        # Подтверждение активации
        complete_activation(api_key=API_KEY, activation_id=activation_id)
        logger.info(f"Активация завершена для профиля {profile_id}.")

        # Активируем холд
        await activate_hold(profile_id)

    except Exception as e:
        logger.error(f"Ошибка в процессе профиля {profile_id}: {e}")
        if activation_id:
            cancel_activation(api_key=API_KEY, activation_id=activation_id)
    finally:
        logger.info(f"Завершение обработки профиля {profile_id}.")

# Обработка группы профилей
async def process_profile_group(profile_group, API_KEY, delay_between_profiles):
    """
    Обрабатывает профили из одной группы с ротацией.
    """
    for profile_id in profile_group:
        await process_registration_async(profile_id, API_KEY)
        logger.info(f"Профиль {profile_id} обработан. Задержка {delay_between_profiles} секунд перед следующим профилем.")
        await asyncio.sleep(delay_between_profiles)

# Главная функция
async def main():
    """
    Главная асинхронная функция для обработки групп профилей.
    """
    profile_groups = [
        ["548173965", "548487604", "548488661"],
        ["548504724", "548495369", "548495465"]
    ]   
    sms_api_key = 'your_sms_api_key'
    delay_between_profiles = 10

    tasks = [
        asyncio.create_task(process_profile_group(group, API_KEY, delay_between_profiles))
        for group in profile_groups
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка в главной функции: {e}")


















