from django.urls import path
from .views import stock_details, predict_stock

urlpatterns = [
    path('', stock_details, name='stock_details'),
    path('predict_stock/<str:s>/<int:d>/', predict_stock, name='predict_stock'),
]
