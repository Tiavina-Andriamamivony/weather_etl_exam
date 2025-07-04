import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_current_weather(city: str, api_key: str) -> dict:
    """Récupère les données météo actuelles pour une ville"""
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric',
            'lang': 'fr'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return {
            'ville': city,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'temperature': data['main']['temp'],
            'humidite': data['main']['humidity'],
            'pluie': data.get('rain', {}).get('1h', 0),
            'vent': data['wind']['speed'],
            'description': data['weather'][0]['description']
        }
        
    except Exception as e:
        logging.error(f"Erreur pour {city}: {str(e)}")
        return None

def calculate_weather_score(weather_data: dict) -> dict:
    """Calcule un score météo basé sur les critères"""
    if not weather_data:
        return None
    
    # Calcul des scores individuels
    temp_score = max(0, 100 - 5 * abs(weather_data['temperature'] - 25))
    rain_score = 100 - min(100, weather_data['pluie'] * 10)
    wind_score = 100 - min(100, weather_data['vent'] * 5)
    
    # Score global pondéré
    global_score = 0.5 * temp_score + 0.3 * rain_score + 0.2 * wind_score
    
    # Ajout des scores aux données
    weather_data.update({
        'score_meteo': round(global_score),
        'ideal_temp': 22 <= weather_data['temperature'] <= 28,
        'low_rain': weather_data['pluie'] < 5,
        'low_wind': weather_data['vent'] < 15
    })
    
    return weather_data

def analyze_cities(cities: list, api_key: str):
    """Analyse les villes et sauvegarde les résultats"""
    results = []
    
    for city in cities:
        logging.info(f"Traitement de {city}...")
        data = get_current_weather(city, api_key)
        if data:
            scored_data = calculate_weather_score(data)
            results.append(scored_data)
    
    if results:
        df = pd.DataFrame(results)
        os.makedirs("weather_results", exist_ok=True)
        df.to_csv(f"weather_results/analyse_meteo_{datetime.now().strftime('%Y%m%d')}.csv", index=False)
        
        # Affichage des meilleures villes
        best_cities = df.sort_values('score_meteo', ascending=False)
        print("\nMeilleures villes pour visiter aujourd'hui:")
        print(best_cities[['ville', 'score_meteo', 'temperature', 'pluie', 'vent']].head())

if __name__ == "__main__":
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    VILLES = ["Antananarivo", "Toamasina", "Mahajanga", "Antsirabe", "Antalaha"]

    if not API_KEY:
        logging.error("La clé API OPENWEATHER_API_KEY n'est pas définie")
    else:
        analyze_cities(VILLES, API_KEY)