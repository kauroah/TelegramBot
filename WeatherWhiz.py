import telebot
import requests
import speech_recognition as sr
from telebot import types
from pydub import AudioSegment
import os

# API Keys
API_KEY = '7238852123:AAEg3Q_eLjazC-uTwA1t560nDJ0YcKf7aOw'
WEATHER_API_KEY = 'b1d4b2cfb62107065d96dc99e50c1297'
GEOCODE_API_KEY = '66bf31ef422d3414118720oqla387ae'

# Initialize the bot
bot = telebot.TeleBot(API_KEY)

# Function to get weather by city name
def get_weather_by_city(city):
    """Get the weather information for a given city."""
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric'
    response = requests.get(url)
    data = response.json()

    if data["cod"] != "404":
        main = data["main"]
        weather_desc = data["weather"][0]["description"]
        temp = main["temp"]
        temp_feel = main["feels_like"]

        weather = (f"🌤 Weather Information for *{city.capitalize()}*:\n\n"
                   f"📅 Temperature: *{temp:.1f}°C*\n"
                   f"🌡️ Feels Like: *{temp_feel:.1f}°C*\n"
                   f"🌧️ Description: *{weather_desc.capitalize()}*\n"
                   f"💨 Wind Speed: *{data['wind']['speed']} m/s*\n"
                   f"🌫️ Humidity: *{main['humidity']}%*\n")
        return weather
    else:
        return "🚫 *City not found.* Please ensure the city name is correct and try again."

# Function to get city name by geolocation using Maps.co API
def get_city_by_geolocation(lat, lon):
    """Get the city name based on latitude and longitude using Maps.co."""
    geo_url = f"https://geocode.maps.co/reverse?lat={lat}&lon={lon}&api_key={GEOCODE_API_KEY}"
    response = requests.get(geo_url)
    data = response.json()

    if 'address' in data:
        if 'city' in data['address']:
            return data['address']['city']
        elif 'town' in data['address']:
            return data['address']['town']
        elif 'village' in data['address']:
            return data['address']['village']
    return None

# Handler for text messages
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.strip()

    # Check if the message is a command
    if text.startswith('/'):
        if text == '/start' or text == '/help':
            help_text = ("📋 *Welcome to WeatherBot!*\n\n"
                         "I am here to assist you with current weather information in several ways:\n"
                         "- 🌆 *Text Message:* Send me the name of a city to get weather details.\n"
                         "- 🎙️ *Voice Message:* Send me a voice message with the name of a city, and I'll transcribe it and provide the weather details.\n"
                         "- 📍 *Geolocation:* Share your location with me, and I'll provide the weather information for that area.\n\n"
                         "Just type your request, and I'll get the information you need promptly.")
            bot.reply_to(message, help_text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "⚠️ *Unknown command.* Please use /start or /help for assistance.")
    else:
        # Treat the text as a city name
        city = text
        weather_data = get_weather_by_city(city)
        bot.reply_to(message, weather_data, parse_mode='Markdown')

# Handler for voice messages
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    file_info = bot.get_file(message.voice.file_id)
    file = requests.get(f'https://api.telegram.org/file/bot{API_KEY}/{file_info.file_path}')
    
    with open("voice.ogg", 'wb') as f:
        f.write(file.content)
    
    audio = AudioSegment.from_ogg("voice.ogg")
    audio.export("voice.wav", format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile("voice.wav") as source:
        audio = recognizer.record(source)
    
    try:
        city = recognizer.recognize_google(audio)
        weather_data = get_weather_by_city(city)
        bot.reply_to(message, weather_data, parse_mode='Markdown')
    except sr.UnknownValueError:
        bot.reply_to(message, "🗣️ *Sorry, I could not understand the audio.* Please try again.")
    except sr.RequestError:
        bot.reply_to(message, "🌐 *Could not request results from the speech recognition service.* Please try again later.")

    os.remove("voice.ogg")
    os.remove("voice.wav")

# Handler for location messages
@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    city = get_city_by_geolocation(lat, lon)
    if city:
        weather_data = get_weather_by_city(city)
        bot.reply_to(message, weather_data, parse_mode='Markdown')
    else:
        bot.reply_to(message, "🌍 *Sorry, I couldn't find the city for this location.* Please ensure your location is accurate and try again.")

# Start the bot
bot.polling()
