import pandas as pd
import os
from datetime import datetime

def transform_to_star() -> str:
    """
    Transforme les données météo malgaches en schéma en étoile avec :
    - Table de faits : weather_facts
    - Dimensions : villes, dates
    """
    # Configuration des chemins
    input_file = "data/processed/meteo_madagascar_global.csv"
    output_dir = "data/star_schema"
    os.makedirs(output_dir, exist_ok=True)
    
    # Chargement des données
    meteo_data = pd.read_csv(input_file, parse_dates=['date'])
    
    # 1. Dimension Ville
    dim_ville_path = f"{output_dir}/dim_villes.csv"
    villes = meteo_data[['ville']].drop_duplicates()
    villes['ville_id'] = villes.index + 1
    villes[['ville_id', 'ville']].to_csv(dim_ville_path, index=False)
    
    # 2. Dimension Date
    dim_date_path = f"{output_dir}/dim_dates.csv"
    dates = meteo_data[['date']].drop_duplicates()
    dates['date_id'] = dates['date'].dt.strftime('%Y%m%d').astype(int)
    dates['annee'] = dates['date'].dt.year
    dates['mois'] = dates['date'].dt.month
    dates['jour'] = dates['date'].dt.day
    dates['saison'] = dates['date'].dt.month % 12 // 3 + 1
    dates[['date_id', 'date', 'annee', 'mois', 'jour', 'saison']].to_csv(dim_date_path, index=False)
    
    # 3. Table de faits
    facts = meteo_data.merge(
        villes, on='ville'
    ).merge(
        dates, on='date'
    )
    
    facts_cols = [
        'date_id', 'ville_id', 'temperature', 'humidite', 
        'pluie', 'vent', 'score_meteo', 'ideal_temp', 
        'low_rain', 'low_wind'
    ]
    
    facts_path = f"{output_dir}/facts_meteo.csv"
    facts[facts_cols].to_csv(facts_path, index=False)
    
    print(f"✅ Transformation réussie. Schéma en étoile généré dans {output_dir}")
    print(f" - Villes: {len(villes)} entrées")
    print(f" - Dates: {len(dates)} entrées")
    print(f" - Mesures: {len(facts)} enregistrements")
    
    return facts_path

if __name__ == "__main__":
    transform_to_star()