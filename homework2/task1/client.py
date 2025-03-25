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
 
def send_command(server_ip, server_port, command):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((server_ip, server_port))
        client_socket.send(command.encode('utf-8'))
        
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Сервер отправил ответ: {response}")
    
    finally:
        client_socket.close()

def register_user(server_ip, server_port, login, password):
    command = f"command:reg; login:{login}; password:{password}"
    send_command(server_ip, server_port, command)

def signin_user(server_ip, server_port, login, password):
    command = f"command:signin; login:{login}; password:{password}"
    send_command(server_ip, server_port, command)

server_ip = '127.0.0.1' # Почему необходимо использовать '127.0.0.1'
server_port = 12345

register_user(server_ip, server_port, "marina", "12345")
register_user(server_ip, server_port, "kirill", "54321")
register_user(server_ip, server_port, "marina", "12345")

signin_user(server_ip, server_port, "marina", "12345")
signin_user(server_ip, server_port, "kirill", "54321")
signin_user(server_ip, server_port, "kirill1", "54321")
