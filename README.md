# Application for getting and working with orders in service center

Based on:  
Telegram bot (aiogram) as frontend
Django framework as backend

# Project objectives

This project was written for service center. 
Its main purposes are:
1. give ability for potential customer to ask fast answer question, take a feedback and make an order for the repair of portable electronics such as smartphone, tablet, laptop, etc.
2. give for masters simple, effective and cheap tool to fast communication with customers.

# Basic functionality

It is three basic roles in this app:
1. Administrator
2. Master
3. Customer

The administrator accepts new orders from customers, assigns masters for each order, receives support messages, and can get a backup copy of the database and log files.
The master works with those orders for which he was appointed by the administrator.
The customer can make new request for repair, can write to support and can talk to master via inline buttons merged with request.

# How to install

For installing app you should clone it from git, make virtual environment and install all dependencies:
```
git clone https://github.com/ilyashirko/service_senter
cd service_center
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```
Now you sould create `.env` file in the root folder and put there such information:
```
TELEGRAM_BOT_TOKEN = 
DJANGO_SECRET_KEY = 
ADMIN_BOT_TOKEN = 
ADMIN_TELEGRAM_ID = 
ALLOWED_HOSTS = 
DEBUG = 
```
`TELEGRAM_BOT_TOKEN` - you can get when you create bot with [BotFather](https://t.me/BotFather)
`ADMIN_BOT_TOKEN` - second bot only for the most important messages for admin
`ADMIN_TELEGRAM_ID` - personal telegram id of administrator, person who get new requests from customers

Then you should make migrations, create superuser and you can launch app
```
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
```
Since you need both Django admin panel and telegram bot, launch both processes at the same time:
```
python3 manage.py runserver | python3 manage.py bot
```
and now you can enter Django admin panel, add masters and start working with app