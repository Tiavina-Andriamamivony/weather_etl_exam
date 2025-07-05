from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from scripts.extract import analyze_cities
from scripts.merge import merge_weather_data
from scripts.transform import transform_to_star

# Configuration par défaut
default_args = {
    'owner': 'meteo_madagascar',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Villes malgaches à traiter
MALAGASY_CITIES = [
    "Antananarivo",
    "Toamasina", 
    "Mahajanga",
    "Antsirabe",
    "Antalaha"
]

with DAG(
    'madagascar_weather_etl',
    default_args=default_args,
    description='ETL pour les données météo de Madagascar',
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['weather', 'madagascar'],
) as dag:

    # Tâche d'extraction (unique car votre script gère déjà toutes les villes)
    extract_task = PythonOperator(
        task_id='extract_current_weather',
        python_callable=analyze_cities,
        op_args=[MALAGASY_CITIES, "{{ var.value.OPENWEATHER_API_KEY }}"],
        dag=dag,
    )

    # Tâche de fusion
    merge_task = PythonOperator(
        task_id='merge_weather_data',
        python_callable=merge_weather_data,
        dag=dag,
    )

    # Tâche de transformation
    transform_task = PythonOperator(
        task_id='transform_to_star_schema',
        python_callable=transform_to_star,
        dag=dag,
    )

    # Orchestration des tâches
    extract_task >> merge_task >> transform_task

    # Documentation
    dag.doc_md = """
    ## Pipeline ETL Météo Madagascar
    
    Ce DAG automatise la collecte et le traitement des données météorologiques pour les principales villes malgaches.
    
    **Étapes :**
    1. Extraction des données actuelles via OpenWeather API
    2. Fusion des fichiers CSV par ville
    3. Transformation en schéma en étoile pour l'analyse
    
    **Fréquence :** Exécution quotidienne
    """