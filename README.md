# Generator Kodu TCP Publisher-Subscriber

## Wymagania
- Python 3.10+
- pakiet jinja2

Instalacja zależności:
python3 -m pip install jinja2

## Jak uruchomić
1. Wygeneruj modele z interface.json:
python3 generate_models.py

2. Uruchom serwer (publisher):
python3 tcp_server.py

3. W drugim terminalu uruchom aplikację subscriber:
python3 main.py --limit 10 --threshold 21.8

Aplikacja odbiera publikacje SensorReading, liczy statystyki i wypisuje alert po przekroczeniu progu temperatury.

## Opcjonalnie: prosty klient testowy
python3 tcp_client.py
