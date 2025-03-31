'''
Написать веб-приложение на Flask со следующими ендпоинтами:
    - главная страница - содержит ссылки на все остальные страницы
    - /duck/ - отображает заголовок "рандомная утка №ххх" и картинка утки 
                которую получает по API https://random-d.uk/
                
    - /fox/<int>/ - аналогично утке только с лисой (- https://randomfox.ca), 
                    но количество разных картинок определено int. 
                    если int больше 10 или меньше 1 - вывести сообщение 
                    что можно только от 1 до 10
    
    - /weather-minsk/ - показывает погоду в минске в красивом формате
    
    - /weather/<city>/ - показывает погоду в городе указанного в city
    
    - по желанию добавить еще один ендпоинт на любую тему 
    
    
Добавить обработчик ошибки 404. (есть в example)
    

'''

import re
import os
import requests
from flask import Flask, request, session, redirect, url_for, render_template
from pyowm import OWM
from pyowm.utils.config import get_default_config

config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM('f7ab670dd123e8e33a8296b1d5ebf253', config_dict)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(39).hex()

users = {}

def get_current_user():
    return users.get(session.get('user'))

def is_cyrillic(text):
    return bool(re.fullmatch('[а-яА-ЯёЁ\s]+', text))

def is_valid_login(login):
    return bool(re.fullmatch('^[a-zA-Z0-9_]{6,20}$', login))

def is_valid_password(password):
    return bool(re.fullmatch('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,15}$', password))

@app.route("/")
def index():
    user = get_current_user()

    return render_template('index.html', user=user)

@app.route("/duck/")
def duck():
    try:
        response = requests.get('https://random-d.uk/api/random')
        response.raise_for_status()
        user = get_current_user()
        duck_data = response.json()
        duck_number = duck_data['url'].split('/')[-1].split('.')[0]
        return render_template('duck.html', user=user, duck=duck_data, duck_number=duck_number)
    except Exception as e:
        error_data = {
            'url': 'https://random-d.uk/api/placeholder.jpg',
            'message': 'Упс..! Ошибка'
        }
        return render_template('duck.html', duck=error_data, duck_number="0")


@app.route("/fox/")
@app.route("/fox/<int:num>/")
def fox(num=1):
    if num < 1 or num > 10:
        return render_template('fox.html', message="Можно только от 1 до 10.")
    
    try:
        response = requests.get('https://randomfox.ca/floof/')
        response.raise_for_status()
        user = get_current_user()
        fox_data = response.json()
        
        return render_template('fox.html', user=user, fox=fox_data, fox_number=num, message=None)
    except Exception as e:
        return render_template('fox.html', message="Ошибка получения данных.")

@app.route("/weather/")
@app.route("/weather/<string:city>/")
def weather(city="Minsk"):
    try:
        user = get_current_user()
        weather_manager = owm.weather_manager()
        observation = weather_manager.weather_at_place(city)
        weather = observation.weather
        
        weather_data = {
            'city': city,
            'status': weather.detailed_status,
            'temp': weather.temperature('celsius')['temp'],
            'temp_feels': weather.temperature('celsius')['feels_like'],
        }
        
        return render_template('weather.html', user=user, weather=weather_data, city=city)
    except Exception as e:
        return render_template('weather.html', message=f"Ошибка вывода погоды для {city}")

@app.route("/weather-minsk/")
def weather_minsk():
    return weather('Minsk')

@app.route("/photos/")
def photos():
    try:
        response = requests.get('https://jsonplaceholder.typicode.com/albums/1/photos')
        response.raise_for_status()
        user = get_current_user()
        photos = response.json()

        return render_template('photos.html', user=user, photos=photos)
    except Exception as e:
        return render_template('photos.html', message="Не удалось загрузить фотографии")

@app.route("/sign-up/", methods=['GET', 'POST'])
def sign_up():
    global tmp_email
    user = get_current_user()
    errors = {}
    form = {
        'email': '',
        'password': '',
        'login': '',
        'fullname': '',
        'age': ''
    }

    if request.method == 'POST':
        if not is_cyrillic(request.form.get('fullname')):
            errors['fullname'] = 'Имя и Фамилия обязаны быть кириллицей!'

        if not is_valid_login(request.form.get('login')):
            errors['login'] = 'Некорректный логин!'

        if not is_valid_password(request.form.get('password')):
            errors['password'] = 'Некорректный пароль!'

        form = dict(request.form)

        if errors:
            return render_template('sign-up.html', form=form, errors=errors)
        else:
            if user:
                errors['auth'] = 'Такой пользователь уже существует'
                return render_template('sign-up.html', form=form, errors=errors)

            new_form = form
            new_form['key'] = os.urandom(39).hex()
            users[new_form['email']] = new_form
            return redirect(url_for('sign_in'))

    return render_template('sign-up.html', form=form)

@app.route("/sign-in/", methods=['GET', 'POST'])
def sign_in():
    errors = {}
    form = {
        'password': '',
        'email': ''
    }

    if request.method == 'POST':
        form = dict(request.form)
        session['user'] = form['email']
        user = get_current_user()

        if not user:
            return render_template('sign-in.html', form=form, errors=errors)

        if not user.get('email'):
            errors['email'] = 'Такого email не существует!'
        
        if user.get('password') != form['password']:
            errors['password'] = 'Неправильный пароль!'
        
        if errors:
            return render_template('sign-in.html', form=form, errors=errors)

        return redirect(url_for('index'))

    return render_template('sign-in.html', form=form)

@app.route("/sign-out/")
def sign_out():
    session.pop('user', None)
    return redirect(url_for('sign_in'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error=error)

@app.before_request
def check_auth():
    if request.endpoint in ['sign_in', 'sign_up'] and session.get('user'):
        return redirect(url_for('index'))

    if request.endpoint not in ['sign_in', 'sign_up', 'index'] and not session.get('user'):
        return redirect(url_for('sign_in'))

if __name__ == "__main__":
    app.run(port=3000, debug=True)
