import numpy as np
import scipy.stats as st
import math
from PIL import Image
def start_draw(city, data, MIN_LAT, MIN_LON, MAX_LAT, MAX_LON):
     MAXX = 800
     MAXY = 800
     power = 2.0
     smoothing = 2
     grid = np.zeros((MAXX, MAXY), dtype='float32')
     x, y, v = formatData(data, MAXX, MAXY, MIN_LAT, MIN_LON,MAX_LAT, MAX_LON)
 # Создание изоюражения
 global colors, I, IM, buckets
 I = Image.new('RGBA', (MAXX, MAXY))
 IM = I.load()
 global MINV
 global MAXV
 MINV = min(v)
 MAXV = max(v)
 buckets = np.linspace(max(v), min(v), 15)
 colors = []
 n_colors = len(buckets) + 1
 print(min(v))
 colors = [(43, 0, 1), (84, 16, 41), (114, 22, 56), (147, 23,
78), (225, 94, 93), (233, 143, 67), (234, 185, 57),
 (235, 224, 53),
 (190, 228, 61), (108, 209, 80), (78, 194, 98),
(64, 160, 180), (67, 105, 196), (85, 78, 177)
 ]
 # Считаем интрополяцию
 grid = invDist(x, y, v, city, MAXX, MAXY, power, smoothing)
def ll_to_pixel(lat, lon, params, MAX_X, MAX_Y, MIN_LAT,MIN_LON, MAX_LAT, MAX_LON):

     adj_lat = lat - MIN_LAT
     adj_lon = lon - MIN_LON
     delta_lat = MAX_LAT - MIN_LAT
     delta_lon = MAX_LON - MIN_LON
     # x is lon, y is lat
     # 0,0 is MIN_LON, MAX_LAT
     lon_frac = adj_lon / delta_lon
     lat_frac = adj_lat / delta_lat
     x = int(lon_frac * MAX_X)
     y = int((1 - lat_frac) * MAX_Y)
     if params == 'lat':
     return x
     else:
     return y
     # return x
def formatData(data, MAXX, MAXY, MIN_LAT, MIN_LON, MAX_LAT, MAX_LON):
     x = []
     y = []
     v = []
     v1Array = []
     for params in range(len(data)):
     v1 = int(data[params]['priceForMetres'])
     v1Array.append(v1)
     # Отрезаем 1% от значений и ищем максимум и минимум
    получевсшегося массива
     trimValue = st.trimboth(v1Array, 0.01)
     maxValue = max(trimValue)
     minValue = min(trimValue)
     for params in range(len(data)):
         x1 = ll_to_pixel(float(data[params]['building']['lat']),
        float(data[params]['building']['lng']), 'lat', MAXX,
         MAXY, MIN_LAT, MIN_LON, MAX_LAT,
        MAX_LON)
         y1 = ll_to_pixel(float(data[params]['building']['lat']),
        float(data[params]['building']['lng']), 'lon', MAXX,MAXY, MIN_LAT, MIN_LON, MAX_LAT,MAX_LON)
         v1 = int(data[params]['priceForMetres'])
         if 0 <= y1 <= MAXY and 0 <= x1 <= MAXX and minValue < v1
        < maxValue:
             x = np.append(x, x1)
             y = np.append(y, y1)
             v = np.append(v, v1)
     return x, y, v
def color(val, buckets):
     if val == 0:
     return (0, 0, 0, 0)
     for price, color in zip(buckets, colors):
     if val > price:
     return color
     return colors[-1]
def pointValue(x, y, power, smoothing, xv, yv, values):
     nominator = 0
     denominator = 0
     for i in range(0, len(values)):
         dist = np.sqrt((x - xv[i]) * (x - xv[i]) + (y - yv[i]) *
        (y - yv[i]) + smoothing * smoothing);
        points, return the data point value to avoid singularities
         if (dist < 0.0000001):
            return values[i]
     nominator = nominator + (values[i] / pow(dist, power))
     denominator = denominator + (1 / pow(dist, power))
     if denominator > 0:
        value = nominator / denominator
     else:
        value = 0
     return value
def invDist(xv, yv, values, city, xsize=1000, ysize=1000, power=2, smoothing=0):
     valuesGrid = np.zeros((ysize, xsize))
     for x in range(0, xsize):
        for y in range(0, ysize):
         valuesGrid[y][x] = pointValue(x, y, power,smoothing, xv, yv, values)
         IM[x, y] = color(valuesGrid[y][x], buckets)
         print("Готово:", x, "из", xsize)
     out_fname = str(city) + "TEST" + str(MINV) + "--" +str(MAXV)
     I.save(out_fname + ".png", "PNG")
     return valuesGrid