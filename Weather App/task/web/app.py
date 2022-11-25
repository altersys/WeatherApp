


"""
- installed base python 3.8 (neither 3.9 nor 3.10 were not working even with package versions mentioned below)
- installed Flask 1.1.2 (as recommended),  pyppeteer 1.0.2(against recommendation as advised by community), markupsafe 2.0.1
- moved Pycharm projects directory a folder that does not contain spaces in it's name
- renamed project folder itself to remove spaces
"""

import json
from flask import Flask, flash, redirect, get_flashed_messages
from flask import render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import requests as r
from requests.exceptions import HTTPError, ConnectionError
from urllib.parse import urlencode
import sys

WEATHER_API_ADDRESS = 'http://api.openweathermap.org/data/2.5/weather'
WEATHER_APPID = 'ad9ea2b4e6a7f13c364aa21d2ed8670c' # '9e2efdd903fef87e379f1d8dccdb354c'
WEATHER_UNITS = 'metric'
DB_URI = 'sqlite:///weather.db'
# openweather_api_url = 'http://api.openweathermap.org/data/2.5/weather?q=London&APPID=9e2efdd903fef87e379f1d8dccdb354c'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'So-Seckrekt'

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    #name = db.Column(db.String(80), unique=False, nullable=False)

    def __repr__(self):
        return '<City %r>' % self.name



with app.app_context():
    db.create_all()



def fetch_city_weather(city_name):
    params_dict = {'q': city_name,
                   'APPID': WEATHER_APPID,
                   'units': WEATHER_UNITS}
    weather_dict = {}
    try:
        wx_response = r.get(WEATHER_API_ADDRESS, params=params_dict)
        if wx_response.ok:
            response_dict = json.loads(wx_response.text)
            weather_dict = {'city_name': response_dict.get('name', 'Unknown'),
                           'temperature_celsius': response_dict.get('main', {}).get('temp', 'Unknown'),
                           'current_weather': response_dict.get('weather', {})[0].get('main', 'Unknown')}
        else:
            app.logger.warning(f'Received code {wx_response.status_code} from {WEATHER_API_ADDRESS}')

    except (HTTPError, ConnectionError) as c:
        pass
        # raise
        print(c)
        app.logger.critical(c)
    except KeyError as k:
        app.logger.error(k)
    return weather_dict


def city_names():
    return db.session.query(City.name).all()


def save_city(city_name):
    if city_in_db(city_name):
        return
    city = City(name=city_name)
    db.session.add(city)
    db.session.commit()


def delete_city(city_name):
    q = db.session.query(City)
    q.filter(City.name == city_name).delete()
    db.session.commit()


def city_in_db(city_name):
    return db.session.query(City.name).filter_by(name=city_name).first() is not None


def city_exists(city_name):
    return fetch_city_weather(city_name).get('city_name') is not None


def prepare_weather_page():
    all_wx_dict = {c[0]: fetch_city_weather(c) for c in city_names()}
    return render_template('index.html', wx=all_wx_dict)

@app.route('/', methods=['GET', 'POST'])
def index():
    # all_wx_dict = {}
    if request.method == 'POST':
        if city_in_db(request.form['city_name']):
            flash('The city has already been added to the list!', 'error')
            return prepare_weather_page()
        if not city_exists(request.form['city_name']):
            flash("The city doesn't exist!", 'error')
            return prepare_weather_page()
        save_city(request.form['city_name'])
    return prepare_weather_page()


@app.route('/delete', methods=['POST'])
def delete():
    try:
        # actually in template it is id, but we are referencing name here
        delete_city(request.form['id'])
    finally:
        return redirect('/')

# /add should be moved to /
@app.route('/add')
def add_city():
    pass


@app.route('/profile')
def profile():
    return 'This is profile page'


@app.route('/login')
def login():
    return 'This is login page'


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
