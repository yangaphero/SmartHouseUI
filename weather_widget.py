from kivy.loader import Loader
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
import requests
from requests.exceptions import RequestException


class WeatherWidget(FloatLayout):
    temperature_label = ObjectProperty(None)
    humidity_label = ObjectProperty(None)
    pressure_label = ObjectProperty(None)
    recommendation_label = ObjectProperty(None)
    rain_rating = ObjectProperty(None)
    icon = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(WeatherWidget, self).__init__(*args, **kwargs)
        Clock.schedule_once(self.update_weather, timeout=1)
        Clock.schedule_interval(self.update_weather, timeout=10)

    def update_weather(self, instance):
        try:
            response = requests.get(
                'http://127.0.0.1:10100/sensors/weather/read',
                timeout=(0.05, 0.1),
            )
        except RequestException as ex:
            self.icon.opacity = 0.2
            return

        data = response.json()

        if data['status'] != 'ok':
            self.icon.opacity = 0.2
            return

        self.temperature_label.text = str(round(data['data']['temperature'])) + ' \u00b0C'
        self.humidity_label.text = str(round(data['data']['humidity'])) + ' %'
        self.pressure_label.text = str(round(data['data']['pressure'])) + ' kPa'

        rain_forecast_rating = data['data']['rain_forecast_rating']
        if rain_forecast_rating > 2.0:
            text = 'Take an umbrella!!!'
            color = 1, 0.3, 0.3, 1
        elif rain_forecast_rating > 1.0:
            text = 'High rain chance'
            color = 1, 0.3, 0.3, 1
        elif rain_forecast_rating > 0.5:
            text = 'A small rain is expected'
            color = 1, 0.6, 0.4, 1
        elif rain_forecast_rating > 0.2:
            text = 'A chance of small rain'
            color = 1, 0.8, 0.6, 1
        else:
            text = 'Weather will be good'
            color = 0.2, 0.8, 0.2, 1

        self.rain_rating.text = '%0.2f' % rain_forecast_rating

        self.recommendation_label.text = text
        self.recommendation_label.color = color

        self.icon.source = data['data']['icon_url']
        self.icon.opacity = 1

