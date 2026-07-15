import asyncio
import aiohttp
import schedule
import time
import sys
from datetime import datetime
from telegram import Bot
import os
from dotenv import load_dotenv
import pytz

class WeatherBot:
    def __init__(self, telegram_token, weather_api_key, chat_id, city, time_send='07:00', timezone='Europe/Madrid'):
        self.telegram_token = telegram_token
        self.weather_api_key = weather_api_key
        self.chat_id = chat_id
        self.city = city
        self.time_send = time_send
        self.timezone = pytz.timezone(timezone)
        self.bot = Bot(token=telegram_token)
        
    async def get_weather_data(self):
        """Obtiene datos meteorológicos de OpenWeatherMap API"""
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': self.city,
            'appid': self.weather_api_key,
            'units': 'metric',
            'lang': 'es'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        print("❌ Error 401: API key inválida o no configurada correctamente")
                        print("Verifica tu WEATHER_API_KEY en el archivo .env")
                        return None
                    elif response.status == 404:
                        print(f"❌ Error 404: Ciudad '{self.city}' no encontrada")
                        print("Verifica el nombre de la ciudad en CITY en el archivo .env")
                        return None
                    else:
                        print(f"❌ Error al obtener datos meteorológicos: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Error en la solicitud de clima: {e}")
            return None
    
    async def get_forecast_data(self):
        """Obtiene pronóstico de 5 días para calcular probabilidad de lluvia"""
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': self.city,
            'appid': self.weather_api_key,
            'units': 'metric',
            'lang': 'es'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        print("❌ Error 401: API key inválida para pronóstico")
                        return None
                    elif response.status == 404:
                        print(f"❌ Error 404: Ciudad '{self.city}' no encontrada para pronóstico")
                        return None
                    else:
                        print(f"❌ Error al obtener pronóstico: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Error en la solicitud de pronóstico: {e}")
            return None
    
    def format_weather_message(self, weather_data, forecast_data):
        """Formatea el mensaje con información meteorológica"""
        if not weather_data:
            return "❌ No se pudo obtener información meteorológica"
        
        # Información actual del clima
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        description = weather_data['weather'][0]['description'].title()
        city_name = weather_data['name']
        
        # Calcular probabilidad de lluvia del día
        rain_probability = 0
        if forecast_data:
            today_forecasts = []
            current_date = datetime.now(self.timezone).strftime('%Y-%m-%d')
            
            for forecast in forecast_data['list'][:8]:  # Próximas 24 horas (8 intervalos de 3h)
                forecast_date = forecast['dt_txt'][:10]
                if forecast_date == current_date:
                    if 'rain' in forecast:
                        today_forecasts.append(forecast)
            
            if today_forecasts:
                rain_probability = len(today_forecasts) / len(forecast_data['list'][:8]) * 100
        
        # Emoji según el clima
        weather_emoji = "☀️"
        if "lluvia" in description.lower() or "rain" in description.lower():
            weather_emoji = "🌧️"
        elif "nube" in description.lower() or "cloud" in description.lower():
            weather_emoji = "☁️"
        elif "nieve" in description.lower() or "snow" in description.lower():
            weather_emoji = "❄️"
        elif "tormenta" in description.lower() or "storm" in description.lower():
            weather_emoji = "⛈️"
        
        message = f"""🌤️ **Buenos días! Aquí tienes el clima de hoy**

📍 **{city_name}**
🌡️ **Temperatura:** {temp:.1f}°C (se siente como {feels_like:.1f}°C)
{weather_emoji} **Condiciones:** {description}
💧 **Humedad:** {humidity}%
🌧️ **Probabilidad de lluvia:** {rain_probability:.0f}%

"""
        
        # Agregar recomendaciones
        if rain_probability > 50:
            message += "☂️ **Recomendación:** ¡No olvides llevar paraguas hoy!"
        elif rain_probability > 20:
            message += "🌦️ **Recomendación:** Posibilidad de lluvia, considera llevar paraguas"
        else:
            message += "☀️ **Recomendación:** Día sin lluvia prevista, ¡disfruta!"
        
        message += f"\n\n⏰ Enviado automáticamente a las {datetime.now(self.timezone).strftime('%H:%M')} ({self.timezone.zone})"
        
        return message
    
    async def send_weather_message(self):
        """Envía el mensaje meteorológico"""
        try:
            weather_data = await self.get_weather_data()
            forecast_data = await self.get_forecast_data()
            
            message = self.format_weather_message(weather_data, forecast_data)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            print(f"Mensaje enviado exitosamente a las {datetime.now(self.timezone)}")
            
        except Exception as e:
            print(f"Error al enviar mensaje: {e}")
            # Enviar mensaje de error
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"❌ Error al obtener información meteorológica: {str(e)}"
                )
            except:
                pass
    
    def schedule_daily_message(self):
        """Programa el mensaje diario a la hora configurada"""
        
        # Convertir la hora configurada a UTC para el scheduling
        local_time = datetime.strptime(self.time_send, '%H:%M').time()
        local_dt = datetime.combine(datetime.now().date(), local_time)
        local_aware = self.timezone.localize(local_dt)
        utc_time = local_aware.astimezone(pytz.UTC).time()
        utc_time_str = utc_time.strftime('%H:%M')
        
        schedule.every().day.at(utc_time_str).do(self.run_async_task)
        print(f"Bot programado para enviar mensajes diarios a las {self.time_send} ({self.timezone.zone})")
        print(f"Hora UTC del servidor: {utc_time_str}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
    
    def run_async_task(self):
        """Ejecuta la tarea asíncrona en un hilo separado"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_weather_message())
        finally:
            try:
                loop.close()
            except:
                pass
    
    async def test_message(self):
        """Envía un mensaje de prueba inmediatamente"""
        print("Enviando mensaje de prueba...")
        await self.send_weather_message()

def main():
    # Seteo de la política del bucle de eventos para Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener configuración desde variables de entorno
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    weather_api_key = os.getenv('WEATHER_API_KEY')
    chat_id = os.getenv('CHAT_ID')
    city = os.getenv('CITY', 'Madrid,ES')  # Valor por defecto
    time_send_message = os.getenv('TIME_SEND_MESSAGE', '07:00')  # Valor por defecto
    timezone = os.getenv('TIMEZONE', 'Europe/Madrid')  # Valor por defecto
    
    # Verificar que todas las variables requeridas estén configuradas
    if not telegram_token:
        print("❌ Error: TELEGRAM_TOKEN no está configurado en el archivo .env")
        print("Crea un archivo .env con tu configuración siguiendo el ejemplo .env.example")
        return
    
    if not weather_api_key:
        print("❌ Error: WEATHER_API_KEY no está configurado en el archivo .env")
        print("📝 Pasos para obtener tu API key:")
        print("   1. Ve a https://openweathermap.org/api")
        print("   2. Regístrate o inicia sesión")
        print("   3. Ve a 'API keys' en tu perfil")
        print("   4. Copia tu API key al archivo .env")
        return
    
    if not chat_id:
        print("❌ Error: CHAT_ID no está configurado en el archivo .env")
        print("📝 Para obtener tu Chat ID:")
        print("   1. Habla con @userinfobot en Telegram")
        print("   2. Copia el número que te dé al archivo .env")
        return
    
    # Crear e inicializar el bot
    weather_bot = WeatherBot(
        telegram_token=telegram_token,
        weather_api_key=weather_api_key,
        chat_id=chat_id,
        city=city,
        time_send=time_send_message,
        timezone=timezone
    )
    
    # Opción para enviar mensaje de prueba
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(weather_bot.test_message())
        return
    
    print("Iniciando bot meteorológico...")
    print("Presiona Ctrl+C para detener el bot")
    
    try:
        weather_bot.schedule_daily_message()
    except KeyboardInterrupt:
        print("\nBot detenido por el usuario.")

if __name__ == "__main__":
    main()