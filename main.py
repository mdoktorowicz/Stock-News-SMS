import requests
from twilio.rest import Client
import os
import datetime as dt

today = dt.date.today()
yesterday = today - dt.timedelta(days=1)
day_before_yesterday = yesterday - dt.timedelta(days=1)

num_news_articles = 3
percentage_change_for_alert = 0.05

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
twilio_sid = os.environ['twilio_sid']
twilio_auth_token = os.environ['twilio_auth_token']

from_phone_number = "+xxxxxxxxxxx"
to_phone_number = "+xxxxxxxxxxx"

stock_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": os.environ['stock_server_api_key']
}

news_parameters = {
    "q": "Tesla",
    "from": yesterday,
    "sortBy": "popularity",
    "apiKey": os.environ['news_api_key']
}

# This code gets closing price for the same stock as of yesterday and two days ago.
# Then, these prices are compared to get price change percentage.

price_response = requests.get(STOCK_ENDPOINT, params=stock_parameters)
stock_data = price_response.json()
yesterday_stock_data = float(stock_data["Time Series (Daily)"][str(yesterday)]["4. close"])
two_days_ago_stock_data = float(stock_data["Time Series (Daily)"][str(day_before_yesterday)]["4. close"])

percentage_change_in_price = (yesterday_stock_data - two_days_ago_stock_data) / two_days_ago_stock_data
print(round(percentage_change_in_price, 3))


# Using news API to get selected number of news articles.

news_response = requests.get(NEWS_ENDPOINT, params=news_parameters)
news_data = news_response.json()
news_articles = news_data['articles'][:(num_news_articles)]


# Adding selected number of articles to a list

articles_to_send = []
articles_to_send.append([article['title']for article in news_articles])
articles_to_send.append([article['description']for article in news_articles])


# Formatting SMS text

def create_message(article_number):
    global articles_to_send
    if percentage_change_in_price > 0:
        message = f"TSLA: 🔺{round(percentage_change_in_price, 2)*100}%\n" \
                  f"Headline: {articles_to_send[0][article_number]}\n" \
                  f"Brief: {articles_to_send[1][article_number]}"
    else:
        message = f"TSLA: 🔻{round(percentage_change_in_price, 2) * 100}%\n" \
                  f"Headline: {articles_to_send[0][article_number]}\n" \
                  f"Brief: {articles_to_send[1][article_number]}"
    return message


# Use Twilio API to send one text message per news article. Only send messages if price change > % threshold (e.g. 5%).

if percentage_change_in_price >= percentage_change_for_alert or \
        percentage_change_in_price <= -percentage_change_for_alert:
    twilio_client = Client(twilio_sid, twilio_auth_token)
    for n in range(num_news_articles):
        twilio_message = twilio_client.messages \
            .create(
            body=create_message(n),
            from_=from_phone_number,
            to=to_phone_number
        )
