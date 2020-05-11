import requests
import ast

def print_dict(thedict):
    for key, value in thedict.items():
        print('Key: ', key)
        print(' Value: ', value)

def print_dict2(d):
    for ele in d.values():
        print("name: ", ele)
        if isinstance(ele,dict):
            for k, v in ele.items():
                print('-- Key: ', k)
                print('--  Value: ', v)
            else:
                print('Key: ', k)
                print(' Value: ', v)
    return

payload = {'lat':36.2, 'lon':-121.25, 'appid':'4cd8ad620ccc9f51006ccb6fda3b3327'}
r = requests.get('http://api.openweathermap.org/data/2.5/weather', params=payload)
'''
r.url
r.text
r.json
r.raw
'''

res = ast.literal_eval(r.text)
#print(res)
coords = res['coord']
lat = coords['lat']
long = coords['lon']
temp_info = res['main']
wind = res['wind']
weather = res['weather'][0]
weather_desc = weather['main']
weather_desc2 = weather['description']
print('Weather: ', weather_desc, weather_desc2)

temp = temp_info['temp']
feels_like = temp_info['feels_like']
temp_min = temp_info['temp_min']
temp_max = temp_info['temp_max']
pressure = temp_info['pressure']
humidity = temp_info['humidity']
windspeed = wind['speed']
winddir = wind['deg']
dtime = res['sys']
sunrise = dtime['sunrise']
sunset = dtime['sunset']

#print_dict2(res)
