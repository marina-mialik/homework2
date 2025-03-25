import socket

def send_http_request(host, port, path):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"
    client_socket.send(request.encode('utf-8'))
    
    response = client_socket.recv(1024).decode('utf-8')
    print("Ответ от сервера:")
    print(response)
    
    client_socket.close()

def send_custom_command(host, port, command):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    client_socket.send(command.encode('utf-8'))
    
    response = client_socket.recv(1024).decode('utf-8')
    print("Ответ от сервера:")
    print(response)
    
    client_socket.close()

def start_client():
    host = '127.0.0.1'
    port = 8000
    
    while True:
        print("\nВыберите тип запроса:")
        print("1. Отправить HTTP-запрос")
        print("2. Отправить команду на регистрацию")
        print("3. Отправить команду входа пользователя")
        print("4. Выход")
        choice = input("Ваш выбор: ")
        
        if choice == '1':
            path = input("Введите путь (например, /, /test/1/, /message/user1/Hello_python/): ")
            send_http_request(host, port, path)
        elif choice == '2':
            login = input("Введите логин: ")
            password = input("Введите пароль: ")
            command = f"command:reg; login:{login}; password:{password}"
            send_custom_command(host, port, command)
        elif choice == '3':
            login = input("Введите логин: ")
            password = input("Введите пароль: ")
            command = f"command:signin; login:{login}; password:{password}"
            send_custom_command(host, port, command)
        elif choice == '4':
            print("Выход из клиента.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

start_client()
    