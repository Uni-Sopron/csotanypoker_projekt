from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from adatbazis import User, Room, get_db_session
from jatek_hatter import jatek, kartya, jatekos
from adatbazis import Base, engine

app = Flask(__name__)  # Create Flask application
socketio = SocketIO(
    app, cors_allowed_origins="*"
)  # Create SocketIO server, allowing CORS from all origins


def reset_database():
    Base.metadata.drop_all(bind=engine)  # törli az összes táblát
    Base.metadata.create_all(bind=engine)


@socketio.on("connect")
def handle_connect() -> None:
    print("Kliens csatlakozott")


jatek_instance = None  # Initialize the game instance


@socketio.on("login")
def handle_login(data: dict) -> None:
    """
    Login event handler.

    This function checks whether the username already exists,
    and if so, verifies if the user is active.

    Args:
        data (dict): Dictionary containing the username.
    """
    db: Session = get_db_session()
    user: Optional[User] = (
        db.query(User).filter(User.username == data["username"]).first()
    )
    username: str = data["username"]
    # Check if the username is already in use
    if (
        user
        and user.is_active
        and user.socket_id
        and user.socket_id != getattr(request, "sid")
    ):
        emit(
            "login_error",
            {"message": "Ez a felhasználónév már foglalt."},
        )
        db.close()
        return

    session["username"] = username  # Store username in session

    if not user:  # If the user does not exist, create a new one
        db.add(
            User(username=username, socket_id=getattr(request, "sid"), is_active=True)
        )
    else:
        user.socket_id = getattr(request, "sid")
        user.set_active(True)  # Mark user as active

        # Check if the user was in an ongoing game
        # if user.current_room_id:
        #     room = db.query(Room).filter(Room.room_id == user.current_room_id).first()
        #     if room and room.game_started:
        #         emit("rejoin_prompt", {"room_id": room.room_id, "room_name": room.name})
        #         db.commit()
        #         db.close()
        #         return

    # Keresünk egy "jatek" nevű szobát, ha nincs, létrehozzuk
    room = db.query(Room).filter(Room.name == "jatek").first()
    if not room:
        # Ha nincs még ilyen szoba, létrehozzuk
        room_id: str = str(uuid.uuid4())
        room = Room(room_id=room_id, name="jatek")
        db.add(room)
        db.commit()

    # A felhasználót hozzáadjuk a szobához
    if user:
        user = db.query(User).filter(User.username == username).first()
    else:
        user = db.query(User).filter(User.username == username).first()

    user.current_room_id = room.room_id
    db.commit()

    # Csatlakozás a szobához
    join_room(room.room_id)

    # Játékosok lekérdezése
    player_names: list = [
        player.username for player in room.players if player.is_active
    ]

    emit(
        "login_success", {"username": username, "screen_state": "waiting"}
    )  # Send the username back to the client

    # Értesítés a többi játékosnak, hogy új játékos csatlakozott
    emit(
        "player_joined",
        {
            "players": player_names,
            "joined_player": username,
        },
        room=room.room_id,
    )

    # Értesítés a csatlakozó játékosnak
    emit(
        "joined_room",
        {
            "room_id": room.room_id,
            "name": room.name,
            "players": player_names,
            "username": username,
        },
    )

    # Ha elég játékos van, el lehet indítani a játékot
    if (
        len(player_names) >= room.player_count
    ):  # Feltételezve, hogy legalább 2 játékos kell
        room.game_started = True
        db.commit()
        emit("start_game", {"players": player_names}, room=room.room_id)
        print("Játék elindult")
        jatekinditas(player_names)

    db.close()


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    db: Session = get_db_session()
    sid = getattr(request, "sid")
    room = db.query(Room).filter(Room.name == "jatek").first()
    user: Optional[User] = db.query(User).filter(User.socket_id == sid).first()
    celzott_jatekos = (
        db.query(User).filter(User.username == data["kivalasztott_jatekos"]).first()
    )
    print(f"{user.username} megnyomta az OK gombot")
    print(f"kivalasztott_lap: {data['kivalasztott_lap']}")
    print(f"kivalasztott_jatekos: {data['kivalasztott_jatekos']}")
    print(f"allitas: {data['lapot_ado_allitasa']}")
    if not data["pass"]:
        jatek_instance.kartya_valasztas(valasztott_kartya_nev=data["kivalasztott_lap"])

    jatek_instance.celzott_jatekos_valasztas(data["kivalasztott_jatekos"])
    if jatek_instance.volt_e_nala():
        emit("hiba", {"message": "Nála már volt"}, to=sid)
    else:
        jatek_instance.kerdeses_kartya = kartya(data["kivalasztott_lap"])
        jatek_instance.allitas(allitas=data["lapot_ado_allitasa"])
        emit(
            "kartya_kapas",
            {
                "jatekos_allitasa": data["lapot_ado_allitasa"],
                "lapot_ado": user.username,
                "celzott_jatekos": celzott_jatekos.username,
            },
            room=room.room_id,
        )
    print("Játékosok kártyáinak kiírása")
    for j in jatek_instance.jatekosok:
        print(f"{j.nev} kezében lévő kártyák: {[k.nev for k in j.kezbenlevo_kartyak]}")
    print("Játékosok kártyáinak kiírása vége")


def kartya_tartalma():
    db: Session = get_db_session()

    room = db.query(Room).filter(Room.name == "jatek").first()
    emit(
        "kartya_tartalma",
        {"lap": jatek_instance.kerdeses_kartya.nev},
        room=room.room_id,
    )


@socketio.on("tipp")
def handle_tipp(data: dict) -> None:
    # db: Session = get_db_session()
    # sid = getattr(request, "sid")
    valasz = data["tipp"]
    # user: Optional[User] = db.query(User).filter(User.socket_id == sid).first()
    eredmeny = jatek_instance.igaz_vagy_hamis(valasz)
    kartya_tartalma()
    if eredmeny:
        jatek_instance.kartya_lerakas(jatek_instance.aktiv_jatekos)
    else:
        jatek_instance.kartya_lerakas(jatek_instance.celzott_jatekos)

    kartya_lerakas()


@socketio.on("pass")
def handle_pass(data: dict) -> None:
    db: Session = get_db_session()
    sid = getattr(request, "sid")
    room: Room = db.query(Room).filter(Room.name == "jatek").first()
    user: Optional[User] = db.query(User).filter(User.socket_id == sid).first()

    print(f"{user.username} passzolt!")
    jatek_instance.aktiv_jatekos = jatek_instance.celzott_jatekos
    jatek_instance.celzott_jatekos = None

    emit(
        "passzolt",
        {
            "message": f"{user.username} passzolt!",
            "aktiv_jatekos": jatek_instance.aktiv_jatekos.nev,
        },
        room=room.room_id,
    )
    emit(
        "kivalasztott_kartya_tartalma",
        {"lap": jatek_instance.kerdeses_kartya.nev},
        room=user.socket_id,
    )

    print("PASSSSSSSSSSSSSSSSSSSSS")


def kartya_lerakas() -> None:
    db = get_db_session()
    jatekos_adatok = {}
    for j in jatek_instance.jatekosok:
        print(j.elotte_levo_kartyak)
        jatekos_adatok[j.nev] = {
            "elotte_levo_kartyak": j.elotte_levo_kartyak,
            "jatekos_kartyaszam": len(j.kezbenlevo_kartyak),
        }

    for j in jatek_instance.jatekosok:
        user = db.query(User).filter(User.username == j.nev).first()
        if user and user.socket_id:
            kezbenlevo_kartyak = {}
            for k in j.kezbenlevo_kartyak:
                if k.nev in kezbenlevo_kartyak:
                    kezbenlevo_kartyak[k.nev] += 1
                else:
                    kezbenlevo_kartyak[k.nev] = 1
            # kezbenlevo_kartyak = [k.nev for k in j.kezbenlevo_kartyak]
            # elotte_levo_kartyak = [k.nev for k in j.elotte_levo_kartyak]

            emit(
                "jatekos_adatok",
                {
                    "nev": j.nev,
                    "kezbenlevo_kartyak": kezbenlevo_kartyak,
                    # "elotte_levo_kartyak": elotte_levo_kartyak,
                    "kezdo_jatekos": jatek_instance.aktiv_jatekos.nev,
                    "jatekos_adatok": jatekos_adatok,
                },
                to=user.socket_id,
            )


def jatekinditas(jatekosok: list) -> None:
    """
    Start the game with the given players.

    Args:
        jatekosok (list): List of player usernames.
    """
    global jatek_instance
    jatek_instance = jatek([jatekos(felhasznalo) for felhasznalo in jatekosok])
    aktiv_nev = jatek_instance.aktiv_jatekos.nev

    # Pakli kiírása
    print("\n🎴 Pakli lapjai:")
    for idx, kartya_obj in enumerate(jatek_instance.pakli, 1):
        print(f"  {idx}. {kartya_obj.nev}")

    db = get_db_session()
    jatekos_adatok = {}
    for j in jatek_instance.jatekosok:
        print(j.elotte_levo_kartyak)
        jatekos_adatok[j.nev] = {
            "elotte_levo_kartyak": j.elotte_levo_kartyak,
            "jatekos_kartyaszam": len(j.kezbenlevo_kartyak),
        }

    for j in jatek_instance.jatekosok:
        user = db.query(User).filter(User.username == j.nev).first()
        if user and user.socket_id:
            kezbenlevo_kartyak = {}
            for k in j.kezbenlevo_kartyak:
                if k.nev in kezbenlevo_kartyak:
                    kezbenlevo_kartyak[k.nev] += 1
                else:
                    kezbenlevo_kartyak[k.nev] = 1

            emit(
                "jatekos_adatok",
                {
                    "nev": j.nev,
                    "kezbenlevo_kartyak": kezbenlevo_kartyak,
                    # "elotte_levo_kartyak": elotte_levo_kartyak,
                    "kezdo_jatekos": aktiv_nev,
                    "jatekos_adatok": jatekos_adatok,
                },
                to=user.socket_id,
            )


if __name__ == "__main__":
    reset_database()
    socketio.run(app, debug=True, host="0.0.0.0")
