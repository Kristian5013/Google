import requests
import time
import os

# API KEY
api_key = "143095U681e26c0b02080043aa6c22e85ae6d10"

# список ID стран
countries = [4]

# Функция для анализа доступных номеров в разных странах
def check_available_numbers(api_key, max_price=0.0871, min_quantity=5, currency=840):
    for country in countries:
        print(f"Проверка номеров для страны с кодом: {country}")
        url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=getPrices&service=go&country={country}&currency={currency}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for service_code, prices in data.get(str(country), {}).items():
                    for price_str, quantity in prices.items():
                        price = float(price_str)
                        if price <= max_price and quantity >= min_quantity:
                            print(f"Номера доступны по цене {price} с количеством {quantity} для страны {country}.")
                            return country  # Возвращаем код страны при успешной проверке
            print(f"Нет подходящих номеров для страны {country}")
        except ValueError:
            print("Ошибка: Не удалось преобразовать ответ в JSON.")
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения к API smshub: {e}")

    # Пауза перед повторной проверкой всех стран
    time.sleep(3)
    return None  # Если номера не найдены для всех стран

# Функция для получения номера телефона для активации
def get_phone_number(api_key, service="go", country=4, currency=840, max_attempts=5):
    for attempt in range(max_attempts):
        url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=getNumber&service={service}&country={country}&currency={currency}"
        response = requests.get(url)
        if response.status_code == 200 and "ACCESS_NUMBER" in response.text:
            _, activation_id, phone_number = response.text.split(":")
            print(f"Получен номер: {phone_number} (ID активации: {activation_id})")
            return activation_id, phone_number
        elif "NO_NUMBERS" in response.text:
            print(f"Нет доступных номеров на попытке {attempt + 1}/{max_attempts}")
        else:
            print(f"Ошибка при получении номера: {response.text}")
    return None, None


# Основная функция
def activate_number(api_key, max_price=0.0872, min_quantity=5, currency=840, max_attempts=5):
    while True:
        # Анализ рынка
        if check_available_numbers(api_key, max_price, min_quantity, currency):
            # Попытки получения номера
            activation_id, phone_number = get_phone_number(api_key, max_attempts=max_attempts)
            if activation_id and phone_number:
                print(f"Номер успешно получен для активации: {phone_number}")
                # Далее - запустить профиль и зарегистрировать номер
                return activation_id, phone_number
        # Если не удалось, повторить анализ рынка
        print("Не удалось получить номер после попыток, продолжаем анализ рынка.")
        time.sleep(2)  # Интервал до следующего анализа рынка




def complete_activation(api_key, activation_id):
    url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=setStatus&status=6&id={activation_id}"
    response = requests.get(url)
    if response.status_code == 200 and "ACCESS_ACTIVATION" in response.text:
        print("Активация успешно завершена")
    else:
        print(f"Ошибка завершения активации: {response.text}")



def get_sms_code(api_key, activation_id, wait_time=180):
    start_time = time.time()
    while time.time() - start_time < wait_time:
        url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=getStatus&id={activation_id}"
        response = requests.get(url)
        if response.status_code == 200 and "STATUS_OK" in response.text:
            _, code = response.text.split(":")
            print(f"Получен код: {code}")
            return code
        elif "STATUS_WAIT_CODE" in response.text:
            time.sleep(10)
        else:
            print(f"Ошибка при получении кода: {response.text}")
            break
    print("Код не получен в течение отведенного времени.")
    return None




def cancel_activation(api_key, activation_id):
    """Отменяет активацию номера."""
    url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=setStatus&status=8&id={activation_id}"
    requests.get(url)
    print(f"Активация с ID {activation_id} отменена.")


def get_status(api_key, activation_id):
    """Получает текущий статус активации."""
    url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=getStatus&id={activation_id}"
    response = requests.get(url)
    return response.text


def confirm_activation(api_key, activation_id):
    """Подтверждает активацию номера."""
    url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=setStatus&status=6&id={activation_id}"
    requests.get(url)
    print(f"Активация с ID {activation_id} завершена.")



def sync_get_request(url, headers):
    response = requests.get(url, headers=headers)
    return response