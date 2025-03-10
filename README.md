# Csotanypoker_projekt  

## Telepítés: 
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

## src mappába belépés:
    cd src

## Futtatás:

**1.  Szerver indítás:**   (Ebben a változatban nincs értelme elinditani a szervert)  
    python -m csotanypoker.server.main  

**2. Klient inditás:**  (A klient elinditásával megjelenik egy kezdetleges iu felület ami pár gombnyomást érzékel és a terminálban jelzi ki.)   
    python -m csotanypoker.client.client  




**Terminálos verzio inditása:**  
    python -m csotanypoker.terminalos_verzio



**Kétirányú kommunikácio szemléltetése:**
cd poc
flask_socketio:
    1. python flask_server.py
    2. python flask_client.py
socket:
    1. python socket_server.py
    2. python socket_client.py