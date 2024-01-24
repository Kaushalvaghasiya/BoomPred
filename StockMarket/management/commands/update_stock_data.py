from django.core.management.base import BaseCommand
from StockMarket.tasks import update_stock_data
from StockMarket.models import Stocks

class Command(BaseCommand):
    help = 'Updates stock data'

    def handle(self, *args, **options):
        stock_symbols = Stocks.objects.all()

        for stock_symbol in stock_symbols:
            update_stock_data(stock_symbol)

        self.stdout.write(self.style.SUCCESS('Successfully updated stock data'))
