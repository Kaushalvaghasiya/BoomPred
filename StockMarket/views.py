import json
from django.core.serializers.json import DjangoJSONEncoder
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Dropout
from tensorflow.keras.regularizers import l2
from django.shortcuts import redirect, render
from django.urls import reverse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance
from .models import PredictionResults, Stocks, PriceHistory

def stock_details(request):
    stocks = Stocks.objects.all()
    try:
        stock_symbol = request.GET.get('s', '')
        if stock_symbol == "":
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
    volume_json = json.dumps([float(price) for price in price_history.values_list('volume', flat=True)], cls=DjangoJSONEncoder)
    predicted_prices = PredictionResults.objects.filter(stock=stock)
    dates_json = json.dumps([str(date) for date in predicted_prices.values_list('date', flat=True)], cls=DjangoJSONEncoder)
    predicted_prices_json = json.dumps([float(price) for price in predicted_prices.values_list('predicted_price', flat=True)], cls=DjangoJSONEncoder)

    return render(request, 'stock_details.html', {'stock': stock, 'dates_json': dates_json, 'close_prices_json': close_prices_json, 'open_prices_json': open_prices_json, 'low_prices_json': low_prices_json, 'high_prices_json': high_prices_json, 'predicted_prices_json': predicted_prices_json, "volume_json": volume_json, 'stocks': stocks})

def predict_stock(request, s, d=0):
    stock = Stocks.objects.get(stock_symbol=s)
    PredictionResults.objects.filter(stock=stock).delete()
    price_history = PriceHistory.objects.filter(stock=stock)

    data_dict = price_history.values()
    df = pd.DataFrame.from_records(data_dict)
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize('UTC')
    data = df['close_price'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)
    sequence_length = 1
    X, y = [], []
    for i in range(len(scaled_data) - sequence_length):
        seq = scaled_data[i:i + sequence_length]
        label = scaled_data[i + sequence_length]
        X.append(seq)
        y.append(label)
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, kernel_regularizer=l2(0.01), input_shape=(X.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_absolute_error')

    model.fit(X, y, epochs=2, batch_size=32)

    future_days = d + 1
    future_predictions = []

    for i in range(future_days):
        last_sequence = scaled_data[-sequence_length:]
        last_sequence = np.reshape(last_sequence, (1, sequence_length, 1))
        next_prediction = model.predict(last_sequence)
        future_predictions.append(next_prediction)
        scaled_data = np.append(scaled_data, next_prediction, axis=0)

    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

    last_date = df['date'].max()
    future_dates = pd.date_range(start=last_date, periods=future_days + 1)[1:]

    train_predictions = scaler.inverse_transform(model.predict(X))
    train_dates = df['date'].iloc[sequence_length:sequence_length+len(train_predictions)]
    model_used = 'RNN'

    for date, prediction in zip(train_dates, train_predictions):
        PredictionResults.objects.create(
            stock=stock,
            date=date,
            predicted_price=float(prediction[0]),
            confidence_level=0.0,
            model_used=model_used,
        )
    for date, prediction in zip(future_dates, future_predictions):
        PredictionResults.objects.create(
            stock=stock,
            date=date,
            predicted_price=float(prediction[0]),
            confidence_level=0.0,
            model_used=model_used,
        )
    
    return redirect(reverse("stock_details")+ f'?s={stock.stock_symbol}')
    