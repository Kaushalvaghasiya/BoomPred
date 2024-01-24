from datetime import datetime, timedelta
import yfinance as yf
from .models import Stocks, PriceHistory

def update_stock_data(stock_symbol):
    stock = Stocks.objects.filter(stock_symbol=stock_symbol).first()
    latest_date = PriceHistory.objects.filter(stock=stock).latest('date').date
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')

    if start_date <= end_date:
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
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

        print(f"Updated data for {stock_symbol} from {start_date} to {end_date}")
    else:
        print(f"No new data available for {stock_symbol}")
