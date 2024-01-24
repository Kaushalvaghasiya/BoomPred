import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import yfinance
from .models import Stocks, PriceHistory

def stock_details(request):
    stocks = Stocks.objects.all()
    try:
        stock_symbol = request.GET.get('s', '')
        if stock_symbol is "":
            return render(request, 'stock_details.html', {'stocks': stocks})
    except:
        return render(request, 'stock_details.html', {'stocks': stocks})
    try:
        stock = Stocks.objects.get(stock_symbol=stock_symbol)
    except:
        url = f'https://finance.yahoo.com/quote/{stock_symbol}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            company_name = soup.find('h1').text.strip()
            # sector = soup.find('span', text='Sector').find_next('span').text.strip()
            # industry = soup.find('span', text='Industry').find_next('span').text.strip()
            company_name = company_name.split('(')[0].strip()
            stock = Stocks.objects.create(
                stock_symbol=stock_symbol.upper(),
                company_name=company_name,
                sector="",
                industry=""
            )
            stock_data = yfinance.download(stock_symbol)
            for index, row in stock_data.iterrows():
                PriceHistory.objects.create(
                    stock=stock,
                    date=index,
                    open_price=row['Open'],
                    adj_close_price=row['Adj Close'],
                    close_price=row['Close'],
                    high_price=row['High'],
                    low_price=row['Low'],
                    volume=row['Volume']
                )
            print(f"Added historical data for {stock_symbol}")
        except requests.exceptions.RequestException as e:
            return(f"Error fetching stock details for {stock_symbol}: {e}")
        except e:
            return(f"Stock not available {stock_symbol}: {e}")
    price_history = PriceHistory.objects.filter(stock=stock)
    dates_json = json.dumps([str(date) for date in price_history.values_list('date', flat=True)], cls=DjangoJSONEncoder)
    close_prices_json = json.dumps([float(price) for price in price_history.values_list('close_price', flat=True)], cls=DjangoJSONEncoder)
    open_prices_json = json.dumps([float(price) for price in price_history.values_list('open_price', flat=True)], cls=DjangoJSONEncoder)
    low_prices_json = json.dumps([float(price) for price in price_history.values_list('low_price', flat=True)], cls=DjangoJSONEncoder)
    high_prices_json = json.dumps([float(price) for price in price_history.values_list('high_price', flat=True)], cls=DjangoJSONEncoder)

    return render(request, 'stock_details.html', {'stock': stock, 'dates_json': dates_json, 'close_prices_json': close_prices_json, 'open_prices_json': open_prices_json, 'low_prices_json': low_prices_json, 'high_prices_json': high_prices_json, 'stocks': stocks})
