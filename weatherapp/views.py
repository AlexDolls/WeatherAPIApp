from django.shortcuts import render
from django.http import HttpResponse

import requests
from abc import ABC, abstractmethod

from . import tmp_key_file
# Create your views here.

APIkey = tmp_key_file.APIkey


class BaseAPI(ABC):

    @abstractmethod
    def send(self, **querystring):
        pass


class Cache:
    
    def __init__(self):
        self._cache_dict = {}
    
    def add(self, key: str, value: dict):
        if not self._is_exist(key):
            self._cache_dict[key] = value
    
    def remove(self, key: str):
        self._cache_dict.pop(key)

    def get(self, key: str):
        return self._cache_dict.get(key, False)

    def get_full_cache(self):
        return self._cache_dict

    def _is_exist(self, key: str):
        is_exist = self._cache_dict.get(key, False)

        if is_exist:
            return True

        return False


class WeatherCache(Cache):
    pass
                

class DictFormatting(ABC):

    @abstractmethod
    def __init__(self, entrypoint_keys: dict = {"main: Main"}):
        self._entrypoint_keys = entrypoint_keys
        self._match_names = {
                          "temp":"Temperature",
                          "feels_like":"Feels like",
                          "temp_min": "Temp min",
                          "temp_max": "Temp max",
                          "pressure": "Pressure",
                          "humidity": "Humidity"
                        }

    def execute(self, collection: dict):
        res = ""

        for entrypoint in self._entrypoint_keys:
            entrypoint_value = collection.get(entrypoint, False)

            if entrypoint_value:
                try:
                    if entrypoint_value.keys():
                        for subkey in entrypoint_value.keys():
                            matched = self._match_names.get(subkey, False)
                            if matched:
                                res += "{0}:{1}\n".format(matched, entrypoint_value.get(subkey))

                    if not entrypoint_value.keys():
                        res += "{0}:{1}\n".format(self._entrypoint_keys[entrypoint], entrypoint_value)

                except AttributeError:
                    res += "{0}:{1}\n".format(self._entrypoint_keys[entrypoint], entrypoint_value)
        return res


class CurrentWeatherDict(DictFormatting):

    def __init__(self):
        self._entrypoint_keys = {
                                    "main":"Main",
                                 }
        self._match_names = {
                          "temp":"Temperature",
                          "feels_like":"Feels like",
                          "temp_min": "Temp min",
                          "temp_max": "Temp max",
                          "pressure": "Pressure",
                          "humidity": "Humidity",
                        }

    
class GeoCording(BaseAPI):

    def __init__(self, city: str, country_code: str = ""):
        self.city = city
        self.country_code = country_code

    def send(self):
        url = "http://api.openweathermap.org/geo/1.0/direct?q={0},{1}&limit=1&appid={2}".format(self.city, self.country_code, APIkey)

        r = requests.get(url)

        return r.json()[0]


class CurrentWeather(BaseAPI):

    def __init__(
                    self, 
                    geocording: GeoCording,
                    cache: Cache = WeatherCache(),
                    response_formatter: DictFormatting = CurrentWeatherDict()
                ):

        self.geocording = geocording
        self.cache = cache
        self.response_formatter = response_formatter

    def send(self):
        coords = self.geocording.send()

        try:
            lon = coords.get("lon", "0")
            lat = coords.get("lat", "0")
        except AttributeError:
            print("Failed lon/lat finding...")

        result = self.get_from_cache("{}-{}".format(lon, lat))

        if result == False:
            url = "http://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&units=metric&appid={2}".format(lat, lon, APIkey)
            r = requests.get(url)
            self.add_to_cache("{}-{}".format(lon, lat), r.json())
            result = r.json()

        return result
        
    def add_to_cache(self, key: str, value: dict):
        self.cache.add(key, value)

    def get_from_cache(self, key: str):
        return self.cache.get(key)

    def fancy_view(self):
        collection = self.send()
        return self.response_formatter.execute(collection)
        



def get_current_weather(request):
    city = request.GET.get("city", "Kiev")
    country_code = request.GET.get("countrycode", "804")
    
    weather_api_object = CurrentWeather(GeoCording(city, country_code))
    
    weather_info = weather_api_object.fancy_view()
  
    return HttpResponse(weather_info)


