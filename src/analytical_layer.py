import duckdb
import pandas as pd

def build_analytical_layer():
    print("Initializing DuckDB Analytical Layer...")
    
    # 1. Connect to DuckDB (creates a persistent local file)
    con = duckdb.connect('data/weather_lake.duckdb')
    
    # 2. Create the Dimension Table (dim_city) from the CSV
    con.execute("""
        CREATE OR REPLACE TABLE dim_city AS 
        SELECT * FROM read_csv_auto('data/cities.csv')
    """)
    print(" -> dim_city created")
    
    # 3. Clean the raw JSON stream and create the Fact Table (fact_current_weather)
    # This automatically infers the JSON schema, casts the timestamp, and links the city_id
    con.execute("""
        CREATE OR REPLACE TABLE fact_current_weather AS 
        SELECT 
            c.city_id,
            CAST(r.timestamp AS TIMESTAMP) AS record_time,
            CAST(r.temperature_c AS DOUBLE) AS temperature_c,
            CAST(r.precipitation_mm AS DOUBLE) AS precipitation_mm,
            CAST(r.wind_speed_kmh AS DOUBLE) AS wind_speed_kmh
        FROM read_json_auto('data/raw_weather_stream.jsonl') r
        JOIN dim_city c ON r.city = c.city_name
    """)
    print(" -> fact_current_weather created")
    
    # 4. Save tables to Parquet
    con.execute("COPY dim_city TO 'data/dim_city.parquet' (FORMAT PARQUET)")
    con.execute("COPY fact_current_weather TO 'data/fact_current_weather.parquet' (FORMAT PARQUET)")
    print(" -> Data exported to Parquet (Business-Ready Zone)")
    
    # 5. Run an analytical query
    print("\nLatest Weather Conditions")
    result = con.execute("""
        WITH LatestRecords AS (
            SELECT 
                city_id, 
                MAX(record_time) as max_time
            FROM fact_current_weather
            GROUP BY city_id
        )
        SELECT 
            c.city_name, 
            c.country,
            f.temperature_c, 
            f.precipitation_mm,
            f.record_time
        FROM fact_current_weather f
        JOIN LatestRecords lr ON f.city_id = lr.city_id AND f.record_time = lr.max_time
        JOIN dim_city c ON f.city_id = c.city_id
        ORDER BY f.temperature_c DESC
    """).fetchdf()
    
    print(result)
    con.close()

if __name__ == "__main__":
    build_analytical_layer()