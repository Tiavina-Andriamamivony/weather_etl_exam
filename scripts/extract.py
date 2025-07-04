import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WeatherAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_historical_weather(self, city: str, date: datetime) -> Optional[Dict]:
        """
        Récupère les données météo historiques pour une ville à une date spécifique
        Note: L'API historique nécessite un abonnement payant sur OpenWeatherMap
        """
        try:
            timestamp = int(date.timestamp())
            url = f"{self.base_url}/onecall/timemachine"
            params = {
                'lat': None,  # À remplacer par les coordonnées réelles
                'lon': None,  # À remplacer par les coordonnées réelles
                'dt': timestamp,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            # Pour ce script, nous allons simuler des données si l'API historique n'est pas disponible
            # En production, vous devrez implémenter la vraie requête API
            
            # Simulation de données (à remplacer par un vrai appel API)
            simulated_data = {
                'temp': 20 + 10 * (date.month % 12 / 11),  # Variation saisonnière
                'humidity': 70 - 20 * (date.month % 12 / 11),
                'rain': 10 if date.month in [11, 12, 1, 2, 3] else 2,  # Plus de pluie en hiver
                'wind_speed': 5 + 5 * (date.month % 12 / 11),
                'weather': [{'description': 'pluie modérée' if date.month in [11, 12, 1] else 'ciel dégagé'}]
            }
            
            return {
                'temperature': simulated_data['temp'],
                'humidite': simulated_data['humidity'],
                'pluie': simulated_data.get('rain', 0),
                'vent': simulated_data['wind_speed'],
                'description': simulated_data['weather'][0]['description']
            }
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des données historiques pour {city}: {str(e)}")
            return None
    
    def get_current_weather(self, city: str) -> Optional[Dict]:
        """Récupère les données météo actuelles pour une ville"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidite': data['main']['humidity'],
                'pluie': data.get('rain', {}).get('1h', 0) if 'rain' in data else 0,
                'vent': data['wind']['speed'],
                'description': data['weather'][0]['description']
            }
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des données actuelles pour {city}: {str(e)}")
            return None
    
    def analyze_weather_data(self, city: str, weeks: int = 4) -> pd.DataFrame:
        """
        Analyse les données météo sur les dernières semaines et aujourd'hui
        Calcule un score météo basé sur les critères:
        - Température idéale (22-28°C)
        - Faible pluie
        - Faible vent
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        
        weather_data = []
        for date in dates:
            if date.date() == end_date.date():
                data = self.get_current_weather(city)
            else:
                data = self.get_historical_weather(city, date)
                
            if data:
                # Calcul du score météo (0-100)
                temp_score = max(0, 100 - 10 * abs(data['temperature'] - 25))  # Optimal à 25°C
                rain_score = max(0, 100 - 10 * data['pluie']) if data['pluie'] > 0 else 100
                wind_score = max(0, 100 - 10 * data['vent']) if data['vent'] > 3 else 100
                
                # Score global (pondéré)
                global_score = 0.5 * temp_score + 0.3 * rain_score + 0.2 * wind_score
                
                weather_data.append({
                    'ville': city,
                    'date': date.strftime("%Y-%m-%d"),
                    'temperature': data['temperature'],
                    'humidite': data['humidite'],
                    'pluie': data['pluie'],
                    'vent': data['vent'],
                    'description': data['description'],
                    'score_meteo': round(global_score, 1),
                    'ideal_temperature': 22 <= data['temperature'] <= 28,
                    'low_rain': data['pluie'] < 5,
                    'low_wind': data['vent'] < 15
                })
            
            # Pause pour éviter de surcharger l'API
            time.sleep(0.1)
        
        return pd.DataFrame(weather_data)
    
    def get_best_periods(self, df: pd.DataFrame) -> Dict:
        """Détermine les meilleures périodes basées sur les données météo"""
        results = {
            'best_days': [],
            'best_weeks': [],
            'monthly_scores': {}
        }
        
        if df.empty:
            return results
        
        # Meilleurs jours (score > 80)
        best_days = df[df['score_meteo'] > 80].sort_values('score_meteo', ascending=False)
        results['best_days'] = best_days[['date', 'score_meteo', 'temperature', 'pluie', 'vent']].to_dict('records')
        
        # Analyse par semaine
        df['week'] = pd.to_datetime(df['date']).dt.isocalendar().week
        weekly_avg = df.groupby('week').agg({
            'score_meteo': 'mean',
            'temperature': 'mean',
            'pluie': 'mean',
            'vent': 'mean'
        }).reset_index()
        
        best_weeks = weekly_avg[weekly_avg['score_meteo'] > 75].sort_values('score_meteo', ascending=False)
        results['best_weeks'] = best_weeks.to_dict('records')
        
        # Scores par mois (pour recommandation générale)
        df['month'] = pd.to_datetime(df['date']).dt.month
        monthly_scores = df.groupby('month').agg({
            'score_meteo': 'mean',
            'ideal_temperature': 'mean',
            'low_rain': 'mean',
            'low_wind': 'mean'
        })
        
        results['monthly_scores'] = monthly_scores.to_dict('index')
        
        return results
    
    def save_results(self, city: str, df: pd.DataFrame, analysis: Dict):
        """Sauvegarde les résultats dans des fichiers CSV"""
        os.makedirs("weather_analysis", exist_ok=True)
        
        # Sauvegarde des données brutes
        df.to_csv(f"weather_analysis/{city}_weather_data.csv", index=False)
        
        # Sauvegarde de l'analyse
        pd.DataFrame.from_dict(analysis).to_csv(f"weather_analysis/{city}_analysis.csv", index=False)
        
        logging.info(f"Résultats sauvegardés dans le dossier weather_analysis")

def main():
    # Configuration
    API_KEY = "votre_clé_api_openweather"  # Remplacez par votre vraie clé API
    CITIES = ["Paris", "Nice", "Lyon", "Barcelone", "Rome", "Lisbonne"]
    
    analyzer = WeatherAnalyzer(API_KEY)
    
    for city in CITIES:
        logging.info(f"Analyse des données météo pour {city}...")
        
        # Récupération des données
        weather_df = analyzer.analyze_weather_data(city)
        
        if weather_df.empty:
            logging.warning(f"Aucune donnée disponible pour {city}")
            continue
        
        # Analyse des données
        analysis = analyzer.get_best_periods(weather_df)
        
        # Sauvegarde des résultats
        analyzer.save_results(city, weather_df, analysis)
        
        # Affichage des résultats
        print(f"\nAnalyse pour {city}:")
        print("Meilleurs jours:")
        for day in analysis['best_days'][:3]:  # Top 3 seulement
            print(f"- {day['date']}: Score {day['score_meteo']} (Temp: {day['temperature']}°C, Pluie: {day['pluie']}mm, Vent: {day['vent']}km/h)")
        
        print("\nMeilleures semaines:")
        for week in analysis['best_weeks'][:2]:  # Top 2 seulement
            print(f"- Semaine {week['week']}: Score moyen {week['score_meteo']:.1f}")
        
        print("\nScores mensuels moyens:")
        for month, data in analysis['monthly_scores'].items():
            print(f"- Mois {month}: Score {data['score_meteo']:.1f} (Temp idéale {data['ideal_temperature']*100:.0f}%, Faible pluie {data['low_rain']*100:.0f}%, Faible vent {data['low_wind']*100:.0f}%)")

if __name__ == "__main__":
    main()