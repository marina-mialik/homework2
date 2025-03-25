'''
написать приложение-сервер используя модуль socket работающее в домашней 
локальной сети.
Приложение должно принимать данные с любого устройства в сети отправленные 
или через программу клиент или через браузер
    - если данные пришли по протоколу http создать возможность след.логики:
        - если путь "/" - вывести главную страницу
        
        - если путь содержит /test/<int>/ вывести сообщение - тест с номером int запущен
        
        - если путь содержит message/<login>/<text>/ вывести в консоль/браузер сообщение
            "{дата время} - сообщение от пользователя {login} - {text}"
        
        - если путь содержит указание на файл вывести в браузер этот файл
        
        - во всех остальных случаях вывести сообщение:
            "пришли неизвестные  данные по HTTP - путь такой то"
                   
         
    - если данные пришли НЕ по протоколу http создать возможность след.логики:
        - если пришла строка формата "command:reg; login:<login>; password:<pass>"
            - выполнить проверку:
                login - только латинские символы и цифры, минимум 6 символов
                password - минимум 8 символов, должны быть хоть 1 цифра
            - при успешной проверке:
                1. вывести сообщение на стороне клиента: 
                    "{дата время} - пользователь {login} зарегистрирован"
                2. добавить данные пользователя в список/словарь на сервере
            - если проверка не прошла вывести сообщение на стороне клиента:
                "{дата время} - ошибка регистрации {login} - неверный пароль/логин"
                
        - если пришла строка формата "command:signin; login:<login>; password:<pass>"
            выполнить проверку зарегистрирован ли такой пользователь на сервере:                
            
            при успешной проверке:
                1. вывести сообщение на стороне клиента: 
                    "{дата время} - пользователь {login} произведен вход"
                
            если проверка не прошла вывести сообщение на стороне клиента:
                "{дата время} - ошибка входа {login} - неверный пароль/логин"
        
        - во всех остальных случаях вывести сообщение на стороне клиента:
            "пришли неизвестные  данные - <присланные данные>"       
                 

'''

import socket
import re
import os
from datetime import datetime

users = {}

def validate_login_password(login, password):
    if not re.match(r'^[a-zA-Z0-9]{6,}$', login):
        return False
    if len(password) < 8 or not re.search(r'\d', password):
        return False
    return True

def get_html(name: str) -> str:
    try:
        with open(name, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return f"HTTP/1.1 200 OK\n\n{content}"
    except FileNotFoundError:
        raise f"HTTP/1.1 404 Not Found\n\nФайл {name} не найден."

def handle_http_request(request):
    headers = request.split('\n')
    _method, path, _ = headers[0].split()
    
    if path == '/':
        response = get_html('index.html')
    elif path.startswith('/test/'):
        test_number = path.split('/')[2]
        response = f"HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\n\n<h1>Тест с номером {test_number} запущен</h1>"
    elif path.startswith('/message/'):
        parts = path.split('/')
        login = parts[2]
        text = parts[3]

        message = f"{datetime.now()} - сообщение от пользователя {login} - {text}"
        print(message)
        response = f"HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\n\n{message}"
    elif os.path.isfile('.' + path):
        with open('.' + path, 'rb') as file:
            content = file.read()

        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Length: {len(content)}\r\n\r\n"
         ).encode('utf-8') + content
    else:
        response = get_html('not_found.html')
    
    return response

def handle_non_http_request(data):
    if data.startswith("command:reg;"):
        match = re.match(r"command:reg; login:(.*?); password:(.*?)$", data)
        if match:
            login, password = match.groups()
            if validate_login_password(login, password):
                users[login] = password
                response = f"{datetime.now()} - пользователь {login} зарегистрирован"
            else:
                response = f"{datetime.now()} - ошибка регистрации {login} - неверный пароль/логин"
        else:
            response = f"{datetime.now()} - ошибка регистрации - неверный формат данных"
    elif data.startswith("command:signin;"):
        match = re.match(r"command:signin; login:(.*?); password:(.*?)$", data)
        if match:
            login, password = match.groups()
            if login in users and users[login] == password:
                response = f"{datetime.now()} - пользователь {login} произведен вход"
            else:
                response = f"{datetime.now()} - ошибка входа {login} - неверный пароль/логин"
        else:
            response = f"{datetime.now()} - ошибка входа - неверный формат данных"
    else:
        response = f"пришли неизвестные данные - {data}"
    
    return response

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen()
    print("Сервер запущен на порту 8000...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Подключение от {addr}")
        data = client_socket.recv(1024).decode('utf-8')
        
        if data.startswith('GET') or data.startswith('POST'):
            response = handle_http_request(data)
        else:
            response = handle_non_http_request(data)
        
        client_socket.send(response.encode('utf-8'))
        client_socket.close()

start_server()
