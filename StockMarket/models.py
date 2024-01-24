from django.db import models

class Stocks(models.Model):
    stock_symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=255)
    sector = models.CharField(max_length=50)
    industry = models.CharField(max_length=50)

    def __str__(self):
        return self.stock_symbol

class PriceHistory(models.Model):
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE)
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    adj_close_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.IntegerField()

    def __str__(self):
        return f"{self.stock.stock_symbol} - {self.date}"

class FinancialIndicators(models.Model):
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE)
    date = models.DateField()
    indicator_type = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.stock.stock_symbol} - {self.date} - {self.indicator_type}"

class MarketSentiment(models.Model):
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE)
    date = models.DateField()
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=2)
    news_headline = models.TextField()
    news_content = models.TextField()

    def __str__(self):
        return f"{self.stock.stock_symbol} - {self.date}"

class PredictionResults(models.Model):
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE)
    date = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2)
    model_used = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.stock.stock_symbol} - {self.date} - {self.model_used}"
