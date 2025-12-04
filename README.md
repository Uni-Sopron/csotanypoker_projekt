# Csotanypoker_projekt  
## Futtatási módok
A játéknak két futtatási módja van:
### 1. CsotanyPoker.exe futtatása
Töltsd le a **CsotanyPoker.exe** fájlt az alábbi linkről:
- https://github.com/Uni-Sopron/csotanypoker_projekt/releases/tag/v1.1.0

**Megjegyzés:** A vírusirtó szoftver figyelmeztetést adhat a letöltésnél, de az alkalmazás biztonságos.

Az exe futtatása automatikusan a Railway szerverre fog kapcsolódni.  

### 2. Lokális futtatás
Ha szeretnéd lokálisan futtatni a szervert és a klienst, kövesd az alábbi lépéseket:

#### **Telepítés:**
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
#### **Futtatás:**
**Szerver lokális futtatása:**    

    python -m csotanypoker.server.server 

**Kliens indítása:**

    python -m csotanypoker.client.main  

## SRC mappában lévő  egyéb fájlok futtatásához:
### src mappába belépés:
    cd src

**1.  Szerver indítás:**   (Ebben a változatban nincs értelme elindítani a szervert) 

    python -m csotanypoker.server.main  

**2. Klient indítása:**  (A klient elindításával megjelenik egy kezdetleges ui felület ami pár gombnyomást érzékel és a terminálban jelzi ki ezt.)

    python -m csotanypoker.client.client  




**Terminálos verzio indítása:**  

    python -m csotanypoker.terminalos_verzio  



**Kétirányú kommunikácio szemléltetése:**  

- flask_socketio: 
    1. python poc\flask_server.py  
    2. python  poc\flask_client.py  

- socket:  
    1. python  poc\socket_server.py  
    2. python  poc\socket_client.py  

- flask_socketio + Gui:  
    1. python poc\flask_server.py  
    2. python  poc\gui_client.py  

- Asztalok_kezelése:
    1. python poc\asztalos_verzio\server.py  
    2. python poc\asztalos_verzio\main.py

