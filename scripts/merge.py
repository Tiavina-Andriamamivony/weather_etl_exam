# merge.py
import pandas as pd
import os
from datetime import datetime

def merge_weather_data() -> str:
    """
    Fusionne tous les fichiers CSV météo de Madagascar depuis data/weather_results
    vers un fichier global dans data/processed/
    """
    # Chemins
    input_dir = "data/weather_results"
    output_file = "data/processed/meteo_madagascar_global.csv"
    
    # Vérification du dossier source
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Dossier {input_dir} introuvable")
    
    # Création des dossiers de destination
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Liste tous les fichiers CSV
    all_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    
    if not all_files:
        raise ValueError("Aucun fichier CSV trouvé dans data/weather_results")
    
    # Fusion des fichiers
    dfs = []
    for filename in all_files:
        filepath = os.path.join(input_dir, filename)
        try:
            df = pd.read_csv(filepath)
            
            # Standardisation des colonnes
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Vérification des colonnes minimales
            required_cols = {'ville', 'date', 'temperature', 'pluie', 'vent'}
            if not required_cols.issubset(df.columns):
                print(f"Fichier {filename} ignoré (colonnes manquantes)")
                continue
                
            dfs.append(df)
        except Exception as e:
            print(f"Erreur avec {filename}: {str(e)}")
            continue
    
    if not dfs:
        raise ValueError("Aucune donnée valide à fusionner")
    
    # Concaténation et nettoyage
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df['date'] = pd.to_datetime(merged_df['date'])
    merged_df = merged_df.drop_duplicates(subset=['ville', 'date'], keep='last')
    merged_df = merged_df.sort_values(['ville', 'date'])
    
    # Sauvegarde
    merged_df.to_csv(output_file, index=False)
    print(f"✅ Fusion réussie : {len(merged_df)} lignes dans {output_file}")
    
    return output_file

if __name__ == "__main__":
    merge_weather_data()