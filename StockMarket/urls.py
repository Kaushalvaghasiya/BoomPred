from django.urls import path
from .views import stock_details

urlpatterns = [
    path('', stock_details, name='stock_details'),
]
