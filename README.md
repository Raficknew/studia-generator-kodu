# Generator Kodu TCP Publisher-Subscriber

## Temat
Generator kodu ktory wygeneruje serializacje i deseralizacje danych, generator ma wygenerowac metody serializacji i deserializacji do formatu binarnego

## Wymagania
- Python 3.10+
- pakiet jinja2

Instalacja zależności:
python3 -m pip install jinja2

## Jak uruchomić
1. Wygeneruj modele z interface.json:
python3 generate_models.py

2. Uruchom jeden launcher, który startuje serwer i klienta razem:
python3 main.py --limit 10

Launcher startuje serwer publisher i klient subscriber w jednym procesie. Aplikacja odbiera publikacje SensorReading i wypisuje je na ekran.
Launcher nie ruszy bez wygenerowanego [generated_models.py](generated_models.py). Najpierw uruchom `python3 generate_models.py`.
Klient wysyła też własne pakiety SensorReading do serwera, a serwer je wypisuje w logu.

Uwaga: `tcp_client.py` i `tcp_server.py` są modułami pomocniczymi. Direct run kończy się komunikatem `Run main.py instead`.
