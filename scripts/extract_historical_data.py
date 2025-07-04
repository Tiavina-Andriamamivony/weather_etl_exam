import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import math

# Configuration
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=4*365)).strftime('%Y-%m-%d')  # 4 ans

# Créer le dossier weather_results s'il n'existe pas
os.makedirs('weather_results', exist_ok=True)

# Liste des villes avec leurs coordonnées
villes = [
    {"nom": "Antananarivo", "lat": -18.8792, "lon": 47.5079},
    {"nom": "Toamasina", "lat": -18.1499, "lon": 49.4023},
    {"nom": "Mahajanga", "lat": -15.7167, "lon": 46.3167},
    {"nom": "Antsirabe", "lat": -19.8659, "lon": 47.0333},
    {"nom": "Antalaha", "lat": -14.9003, "lon": 50.2788}
]

def get_weather_data(lat, lon, start_date, end_date):
    """Récupère les données météo depuis l'API Open-Meteo"""
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
    """Convertit le code météo en description textuelle"""
    weather_map = {
        0: "ciel dégagé",
        1: "peu nuageux",
        2: "partiellement nuageux",
        3: "nuageux",
        45: "brouillard",
        48: "brouillard givrant",
        51: "bruine légère",
        53: "bruine modérée",
        55: "bruine dense",
        56: "bruine verglaçante légère",
        57: "bruine verglaçante dense",
        61: "pluie légère",
        63: "pluie modérée",
        65: "pluie forte",
        66: "pluie verglaçante légère",
        67: "pluie verglaçante forte",
        71: "neige légère",
        73: "neige modérée",
        75: "neige forte",
        77: "grains de neige",
        80: "averses de pluie légères",
        81: "averses de pluie modérées",
        82: "averses de pluie violentes",
        85: "averses de neige légères",
        86: "averses de neige fortes",
        95: "orage léger ou modéré",
        96: "orage avec grêle légère",
        99: "orage avec grêle forte"
    }
    return weather_map.get(code, "inconnu")

def calculate_weather_score(temp, rain, wind, humidity):
    """Calcule un score météo personnalisé (0-100)"""
    # Pondérations (ajustables)
    temp_weight = 0.5
    rain_weight = -0.3
    wind_weight = -0.1
    humidity_weight = -0.1
    
    # Normalisation
    temp_norm = min(max((temp - 10) / (30 - 10), 0), 1)  # 10-30°C idéal
    rain_norm = 1 - min(rain / 10, 1)  # 0mm=parfait, 10mm=très mauvais
    wind_norm = 1 - min(wind / 15, 1)  # 0km/h=parfait, 15km/h=très mauvais
    humidity_norm = 1 - abs(humidity - 60) / 60  # 60%=idéal
    
    # Calcul du score
    score = (temp_weight * temp_norm + 
             rain_weight * (1 - rain_norm) + 
             wind_weight * (1 - wind_norm) + 
             humidity_weight * (1 - humidity_norm))
    
    return min(max(int(score * 100), 0), 100)

def process_weather_data(data, ville):
    """Transforme les données brutes en format désiré"""
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
    
    # Nettoyage des données
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    
    # Conversion et calculs supplémentaires
    df["description"] = df["weather_code"].apply(weather_code_to_description)
    df["score_meteo"] = df.apply(
        lambda x: calculate_weather_score(
            x["temperature"], 
            x["pluie"], 
            x["vent"], 
            x["humidite"]
        ), axis=1
    )
    
    # Ajout des indicateurs booléens
    df["ideal_temp"] = (df["temperature"] >= 20) & (df["temperature"] <= 28)
    df["low_rain"] = df["pluie"] < 1
    df["low_wind"] = df["vent"] < 15
    
    # Sélection des colonnes finales
    final_cols = [
        "ville", "date", "temperature", "humidite", "pluie", "vent",
        "description", "score_meteo", "ideal_temp", "low_rain", "low_wind"
    ]
    
    return df[final_cols]

# Traitement séparé pour chaque ville
for ville in villes:
    print(f"\nTraitement de {ville['nom']} ({start_date} au {end_date})...")
    raw_data = get_weather_data(ville["lat"], ville["lon"], start_date, end_date)
    
    if raw_data:
        processed_data = process_weather_data(raw_data, ville["nom"])
        
        if processed_data is not None:
            # Génération du nom de fichier
            nom_fichier = f"{ville['nom']}_{start_date}_{end_date}.csv"
            chemin_complet = os.path.join('weather_results', nom_fichier)
            
            # Export en CSV
            processed_data.to_csv(chemin_complet, index=False, float_format="%.2f")
            print(f"Données sauvegardées dans : {chemin_complet}")
            print(f"Nombre de jours : {len(processed_data)}")
            print("Aperçu des premières lignes :")
            print(processed_data.head())
            print("Aperçu des dernières lignes :")
            print(processed_data.tail())
        else:
            print(f"Erreur de traitement des données pour {ville['nom']}")
    else:
        print(f"Échec de récupération des données pour {ville['nom']}")

print("\nTraitement terminé pour toutes les villes !")