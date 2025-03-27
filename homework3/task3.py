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

from flask import Flask, render_template
import requests
from pyowm import OWM
from pyowm.utils.config import get_default_config

config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM('f7ab670dd123e8e33a8296b1d5ebf253', config_dict)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/duck/")
def duck():
    try:
        response = requests.get('https://random-d.uk/api/random')
        response.raise_for_status()
        duck_data = response.json()
        duck_number = duck_data['url'].split('/')[-1].split('.')[0]
        return render_template('duck.html', duck=duck_data, duck_number=duck_number)
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
        fox_data = response.json()
        
        return render_template('fox.html', fox=fox_data, num=num, message=None)
    except Exception as e:
        return render_template('fox.html', message="Ошибка получения данных.")

@app.route("/weather/")
@app.route("/weather/<string:city>/")
def weather(city="Minsk"):
    try:
        weather_manager = owm.weather_manager()
        observation = weather_manager.weather_at_place(city)
        weather = observation.weather
        
        weather_data = {
            'city': city,
            'status': weather.detailed_status,
            'temp': weather.temperature('celsius')['temp'],
            'temp_feels': weather.temperature('celsius')['feels_like'],
        }
        
        return render_template('weather.html', weather=weather_data, city=city)
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
        photos = response.json()

        return render_template('photos.html', photos=photos)
    except Exception as e:
        return render_template('photos.html', message="Не удалось загрузить фотографии")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error=error)

if __name__ == "__main__":
    app.run(port=3000, debug=True)
