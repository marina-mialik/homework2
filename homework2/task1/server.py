"""

написать приложение-клиент используя модуль socket работающее в домашней 
локальной сети.
Приложение должно соединятся с сервером по известному адрес:порт и отправлять 
туда текстовые данные.

известно что сервер принимает данные следующего формата:
    "command:reg; login:<login>; password:<pass>" - для регистрации пользователя
    "command:signin; login:<login>; password:<pass>" - для входа пользователя
    
    
с помощью программы зарегистрировать несколько пользователей на сервере и произвести вход


"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 12345)) # Почему необходимо использовать '0.0.0.0' 
server_socket.listen(1)

store = {}

print("Сервер запущен и ожидает подключений...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Клиент подключился: {client_address}")

    data = client_socket.recv(1024).decode()
    print(f"Клиент отправил данные: {data}")

    if not data:
        print("Клиент отправил пустые данные.")
        client_socket.close()
        continue

    try:
        parts = data.split('; ')
        if len(parts) != 3:
            raise ValueError("Неверный формат данных")

        command, login, password = parts
        command_type, command_value = command.split(':')
        login_type, login_value = login.split(':')
        password_type, password_value = password.split(':')

        if command_value == 'reg':
            if login_value in store:
                response = "The user is already registered..."
            else:
                store[login_value] = {'password': password_value, 'login': login_value}
                response = "The user is registered!"

        elif command_value == 'signin':
            if login_value in store and store[login_value]['password'] == password_value:
                response = "The user is logged in!"
            else:
                response = "There's no such user or password is incorrect..."

        else:
            response = "Unknown command."

    except Exception as e:
        response = f"Error: {str(e)}"

    client_socket.send(response.encode('utf-8'))
    print(f"Ответ сервера: {response}")

    client_socket.close()
