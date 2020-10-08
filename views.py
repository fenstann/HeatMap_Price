from rest_framework import generics
from rest_framework.mixins import *
from rest_framework.views import APIView
from backend.parsing.models import *
from api.map.serializers import *

class SellListView(generics.GenericAPIView):
    queryset = SellList.objects.prefetch_related('building')
    serializer_class = SellListSerializers

class CityList(APIView):
    def get(self,request):
        queryset = City.objects.values()
        serializer = CitySerializers(queryset,  read_only=True, many=True)
        return Response(serializer.data)

class SellListMap(APIView):
    def get(self, request):
        city = request.GET.get("city")
        room = request.GET.get("room")
        queryset = SellList.objects.filter(cityName=city).prefetch_related('building')
        serializer = SellListSerializers(queryset, many=True)
        return Response(serializer.data)

#Получаем все квартиры с ценой, в радиусе пришедшей точки
class ListDistance(APIView):
    def get(self,request):

        # Поумолчанию радиус = 500м, Делим на 100к, чтобы перевести внужный форма
        radius = float((request.GET.__getitem__('radius'))) / 100000
        lat = float(request.GET.__getitem__('lat'))
        lng = float(request.GET.__getitem__('lng'))

        if radius >0.01:
            return Response({'Error':'Дистанция больше 1 км','Code':'1'})
        if radius <0.0005:#50 метров
            return Response({'Error':'Дистанция меньше 50 м','Code':'2'})
        if lat == 0.00000 or lng == 0.00000:
            return Response({'Error': 'Неправельные координаты', 'Code': '3'})

        sqlquery = (
            'SELECT s."fullPriceRub" as fullPriceRub,b.lat,b.lng,b.id '+
            'FROM parsing_buildings as b '+
            'INNER JOIN parsing_selllist as s '+
            'ON b.id = s.building_id '+
            'WHERE |/((lat - %s)^2 + (lng - %s)^2 ) <= %s')

        serializer = ListDistanceSerializers(Buildings.objects.raw(sqlquery,[lat,lng,radius]), many=True, read_only=True)

        if len(serializer.data) <=5:
            return Response({'Error': 'Объявлений меньше 5', 'Code': '3'})
        return Response(serializer.data)





class CitySerializers(serializers.ModelSerializer):
    """Координаты дома"""
    class Meta:
        model = City
        fields = ('id','url','name')

class BuildingsSerializers(serializers.ModelSerializer):
    """Координаты дома"""
    class Meta:
        model = Buildings
        fields = ('lat','lng')



class SellListSerializers(serializers.ModelSerializer):
    '''Список домов с координатами и ценами'''
    building = BuildingsSerializers()
    class Meta:
        model = SellList
        fields = ( 'fullPriceRub',
                  'priceForMetres',
                   'room',
                  'building')


class roomSerializers(serializers.HyperlinkedModelSerializer):
    '''Список комнат'''
    class Meta:
        model = Rooms
        fields = ('id','room')

class priceListSellSerializers(serializers.HyperlinkedModelSerializer):
    """Цены домов"""
    room = roomSerializers()
    class Meta:
        model = SellList
        fields = ('fullPriceRub','fullPriceDollars','priceForMetres','idAvito','room','agent')

class ListDistanceSerializers(serializers.HyperlinkedModelSerializer):
    '''Список домов с координатами и ценами'''

    #price =  serializers.Field(source='SellList.fullPriceRub')
    buildings = priceListSellSerializers(many=True, read_only=True)
    class Meta:
        model = Buildings
        fields = ('buildings','lat','lng')
