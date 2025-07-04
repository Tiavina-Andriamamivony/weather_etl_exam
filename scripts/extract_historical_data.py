import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# Configuration
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=4*365)).strftime('%Y-%m-%d')

# Dossier de sortie
output_dir = "data/weather_results"
os.makedirs(output_dir, exist_ok=True)

villes = [
    {"nom": "Antananarivo", "lat": -18.8792, "lon": 47.5079},
    {"nom": "Toamasina", "lat": -18.1499, "lon": 49.4023},
    {"nom": "Mahajanga", "lat": -15.7167, "lon": 46.3167},
    {"nom": "Antsirabe", "lat": -19.8659, "lon": 47.0333},
    {"nom": "Antalaha", "lat": -14.9003, "lon": 50.2788}
]

def get_weather_data(lat, lon, start_date, end_date):
    url = f"https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,relative_humidity_2m_mean,precipitation_sum,wind_speed_10m_max,weather_code",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur pour {lat},{lon}: {e}")
        return None

def weather_code_to_description(code):
    weather_map = {
        0: "ciel dégagé", 
        1: "peu nuageux",
        # ... (keep your existing weather code mapping)
    }
    return weather_map.get(code, "inconnu")

def calculate_weather_score(temp, rain, wind, humidity):
    temp_weight = 0.5
    rain_weight = -0.3
    wind_weight = -0.1
    humidity_weight = -0.1
    
    temp_norm = min(max((temp - 10) / (30 - 10), 0), 1)
    rain_norm = 1 - min(rain / 10, 1)
    wind_norm = 1 - min(wind / 15, 1)
    humidity_norm = 1 - abs(humidity - 60) / 60
    
    score = (temp_weight * temp_norm + 
             rain_weight * (1 - rain_norm) + 
             wind_weight * (1 - wind_norm) + 
             humidity_weight * (1 - humidity_norm))
    
    return min(max(int(score * 100), 0), 100)

def process_weather_data(data, ville):
    if not data or "daily" not in data:
        return None
    
    df = pd.DataFrame({
        "ville": ville,
        "date": data["daily"]["time"],
        "temperature": data["daily"]["temperature_2m_max"],
        "humidite": data["daily"]["relative_humidity_2m_mean"],
        "pluie": data["daily"]["precipitation_sum"],
        "vent": data["daily"]["wind_speed_10m_max"],
        "weather_code": data["daily"]["weather_code"]
    })
    
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    df["description"] = df["weather_code"].apply(weather_code_to_description)
    df["score_meteo"] = df.apply(
        lambda x: calculate_weather_score(
            x["temperature"], 
            x["pluie"], 
            x["vent"], 
            x["humidite"]
        ), axis=1
    )
    
    df["ideal_temp"] = (df["temperature"] >= 20) & (df["temperature"] <= 28)
    df["low_rain"] = df["pluie"] < 1
    df["low_wind"] = df["vent"] < 15
    
    final_cols = [
        "ville", "date", "temperature", "humidite", "pluie", "vent",
        "description", "score_meteo", "ideal_temp", "low_rain", "low_wind"
    ]
    
    return df[final_cols]

for ville in villes:
    print(f"\nTraitement de {ville['nom']} ({start_date} au {end_date})...")
    raw_data = get_weather_data(ville["lat"], ville["lon"], start_date, end_date)
    
    if raw_data:
        processed_data = process_weather_data(raw_data, ville["nom"])
        
        if processed_data is not None:
            output_path = os.path.join(output_dir, f"{ville['nom']}_{start_date}_{end_date}.csv")
            processed_data.to_csv(output_path, index=False, float_format="%.2f")
            print(f"Données sauvegardées dans : {output_path}")
            print("Aperçu des données :")
            print(processed_data.head())
        else:
            print(f"Erreur de traitement des données pour {ville['nom']}")
    else:
        print(f"Échec de récupération des données pour {ville['nom']}")

print("\nTraitement terminé pour toutes les villes !")