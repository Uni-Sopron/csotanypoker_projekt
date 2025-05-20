from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room
import uuid
from typing import Optional
from sqlalchemy.orm import Session


from jatek_hatter import jatek
import sys
import os

sys.path.append(os.path.abspath(".."))  
from models.model import Jatekos

from adatbazis import Game, User, Room, Card, Player, get_db_session, Base, engine


app = Flask(__name__)
app.secret_key = "titkos_kulcs_ide"  # Session kezeléshez szükséges titkos kulcs
socketio = SocketIO(app, cors_allowed_origins="*")


socketek = {}


def reset_database():  # ez csak teszteléshez kell
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

    if user and user.is_active:
        emit(
            "login_error",
            {"message": "Ez a felhasználónév már foglalt."},
        )

        db.close()
        return

    session["socket_id"] = request.sid
    socketek[username] = session["socket_id"]
    session["username"] = username
    if not user:
        db.add(User(username=username, is_active=True))
    else:
        user.set_active(True)

    room = db.query(Room).filter(Room.name == "jatek").first()
    if not room:
        # Ha nincs még ilyen szoba, létrehozzuk
        room_id: str = str(uuid.uuid4())
        room = Room(room_id=room_id, name="jatek")
        db.add(room)
        db.commit()

    user = db.query(User).filter(User.username == username).first()

    user.current_room_id = room.room_id
    db.commit()

    join_room(room.room_id)

    # Játékosok lekérdezése
    player_names: list = [user.username for user in room.users if user.is_active]

    emit("login_success", {"username": username, "screen_state": "waiting"})
    emit(
        "player_joined",
        {
            "players": player_names,
            "joined_player": username,
        },
        room=room.room_id,
    )

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
    if len(player_names) >= room.player_count:
        room.game_started = True
        db.commit()
        emit("start_game", {"players": player_names}, room=room.room_id)
        print("Játék elindult")
        jatekinditas(player_names)

    db.close()


@socketio.on("oke_click")
def handle_oke_click(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid
    room = db.query(Room).filter(Room.name == "jatek").first()
    game = db.query(Game).filter(Game.room_id == room.room_id).first()
    for lap in jatek_instance.state.pakli:
        if lap.nev == data["kivalasztott_lap"]:
            jatek_instance.state.kerdeses_kartya = lap
            break

    jatek_instance.celzott_jatekos_valasztas(data["kivalasztott_jatekos"])
    jatek_instance.allitas(allitas=data["lapot_ado_allitasa"])

    if not data["pass"]:
        if jatek_instance.van_lap_a_kezeben():
            jatek_vege()
            return
        jatek_instance.kartya_valasztas(
            valasztott_kartya_id=jatek_instance.state.kerdeses_kartya.nev
        )
        player_db = (
            db.query(Player)
            .filter(Player.name == jatek_instance.state.aktiv_jatekos.nev)
            .first()
        )
        card_db = (
            db.query(Card)
            .filter(Card.name == jatek_instance.state.kerdeses_kartya.nev)
            .first()
        )

        if player_db and card_db and card_db in player_db.kezben_levo_lapok:
            player_db.kezben_levo_lapok.remove(card_db)
            db.commit()
        kezbenlevo_kartyak = [
            k.nev for k in jatek_instance.state.aktiv_jatekos.kezbenlevo_kartyak
        ]
        print("jatekos_neve", jatek_instance.state.aktiv_jatekos.nev)
        print("kezbenlevo_kartyak", kezbenlevo_kartyak)
        emit(
            "kezbenlevo_kartyak",
            {
                "kezbenlevo_kartyak": kezbenlevo_kartyak,
            },
            to=sid,
        )

    if (
        jatek_instance.state.celzott_jatekos.nev
        not in jatek_instance.state.kerdeses_kartya.volt_ennel_mar
    ):
        jatek_instance.state.kerdeses_kartya.volt_ennel_mar.append(
            jatek_instance.state.celzott_jatekos.nev
        )
        jatekos_db = (
            db.query(Player)
            .filter(Player.name == jatek_instance.state.celzott_jatekos.nev)
            .first()
        )
        card_db = (
            db.query(Card)
            .filter(Card.name == jatek_instance.state.kerdeses_kartya.nev)
            .first()
        )
        card_db.volt_ennel_mar.append(jatekos_db)
    emit(
        "kartya_kapas",
        {
            "jatekos_allitasa": data["lapot_ado_allitasa"],
            "lapot_ado": jatek_instance.state.aktiv_jatekos.nev,
            "celzott_jatekos": jatek_instance.state.celzott_jatekos.nev,
            "naluk_volt": jatek_instance.state.kerdeses_kartya.volt_ennel_mar,
        },
        room=room.room_id,
    )

    for j in jatek_instance.state.jatekosok:
        player_sid = socketek[j.nev]
        if (
            player_sid
            and j.nev in jatek_instance.state.kerdeses_kartya.volt_ennel_mar
            and j.nev != jatek_instance.state.celzott_jatekos.nev
        ):
            emit(
                "kartya_tartalma",
                {
                    "lap_tipus": jatek_instance.state.kerdeses_kartya.tipus,
                    "lap_sorszam": jatek_instance.state.kerdeses_kartya.sorszam,
                    "naluk_volt": jatek_instance.state.kerdeses_kartya.volt_ennel_mar,
                },
                to=player_sid,
            )

    game.aktiv_jatekos_name = (
        jatek_instance.state.aktiv_jatekos.nev
        if jatek_instance.state.aktiv_jatekos
        else None
    )
    game.celzott_jatekos_name = (
        jatek_instance.state.celzott_jatekos.nev
        if jatek_instance.state.celzott_jatekos
        else None
    )
    game.kerdeses_kartya_name = (
        jatek_instance.state.kerdeses_kartya.nev
        if jatek_instance.state.kerdeses_kartya
        else None
    )
    db.commit()


def kartya_tartalma():
    db: Session = get_db_session()
    room = db.query(Room).filter(Room.name == "jatek").first()
    emit(
        "kartya_tartalma",
        {
            "lap_tipus": jatek_instance.state.kerdeses_kartya.tipus,
            "lap_sorszam": jatek_instance.state.kerdeses_kartya.sorszam,
            "naluk_volt": jatek_instance.state.kerdeses_kartya.volt_ennel_mar,
        },
        room=room.room_id,
    )


@socketio.on("tipp")
def handle_tipp(data: dict) -> None:
    valasz = data["tipp"]
    eredmeny = jatek_instance.igaz_vagy_hamis(valasz)
    kartya_tartalma()
    if eredmeny:
        jatek_instance.kartya_lerakas(jatek_instance.state.aktiv_jatekos)
    else:
        jatek_instance.kartya_lerakas(jatek_instance.state.celzott_jatekos)

    kartya_lerakas()


@socketio.on("pass")
def handle_pass(data: dict) -> None:
    db: Session = get_db_session()
    sid = request.sid

    room: Room = db.query(Room).filter(Room.name == "jatek").first()

    # Ellenőrizzük, hogy a célzott játékos nem None
    if jatek_instance.state.celzott_jatekos is not None:
        jatek_instance.state.aktiv_jatekos = jatek_instance.state.celzott_jatekos
        jatek_instance.state.celzott_jatekos = None

        emit(
            "passzolt",
            {
                "message": f"{jatek_instance.state.aktiv_jatekos.nev} passzolt!",
                "aktiv_jatekos": jatek_instance.state.aktiv_jatekos.nev,
            },
            room=room.room_id,
        )

        emit(
            "kartya_tartalma",
            {
                "lap_tipus": jatek_instance.state.kerdeses_kartya.tipus,
                "lap_sorszam": jatek_instance.state.kerdeses_kartya.sorszam,
                "naluk_volt": jatek_instance.state.kerdeses_kartya.volt_ennel_mar,
            },
            to=sid,
        )
        print(
            "jatek_instance.state.kerdeses_kartya",
            jatek_instance.state.kerdeses_kartya.nev,
        )


def kartya_lerakas() -> None:
    db = get_db_session()
    room = db.query(Room).filter(Room.name == "jatek").first()
    jatekos_adatok = {}
    for j in jatek_instance.state.jatekosok:
        print(j.elotte_levo_kartyak)
        jatekos_adatok[j.nev] = {
            "elotte_levo_kartyak": j.elotte_levo_kartyak,
            "jatekos_kartyaszam": len(j.kezbenlevo_kartyak),
        }

    # Körüzenet küldése a lehelyezett kártyáról
    emit(
        "kartya_lehelyezve",
        {
            "jatekos": jatek_instance.state.aktiv_jatekos.nev,
            "kartya_tipus": jatek_instance.state.kerdeses_kartya.allat_tipus
            if jatek_instance.state.kerdeses_kartya
            else "ismeretlen",
            "aktiv_jatekos": jatek_instance.state.aktiv_jatekos.nev,
        },
        room=room.room_id,
    )

    # A kérdéses kártya nullázása
    jatek_instance.state.kerdeses_kartya = None

    for j in jatek_instance.state.jatekosok:
        player_sid = socketek[j.nev]
        if player_sid:
            kezbenlevo_kartyak = [k.nev for k in j.kezbenlevo_kartyak]
            emit(
                "jatekos_adatok",
                {
                    "nev": j.nev,
                    "kezbenlevo_kartyak": kezbenlevo_kartyak,
                    "kezdo_jatekos": jatek_instance.state.aktiv_jatekos.nev,
                    "jatekos_adatok": jatekos_adatok,
                },
                to=player_sid,
            )

    if jatek_instance.van_4_lap_elotte():
        jatek_vege()


def jatek_vege() -> None:
    db = get_db_session()
    room = db.query(Room).filter(Room.name == "jatek").first()
    game = db.query(Game).filter(Game.room_id == room.room_id).first()
    game.nyertes = jatek_instance.state.aktiv_jatekos.nev
    db.commit()
    emit(
        "jatek_vege",
        {
            "vesztett_jatekos": jatek_instance.state.aktiv_jatekos.nev,
        },
        room=room.room_id,
    )


def jatekinditas(jatekosok: list) -> None:
    """
    Start the game with the given players.

    Args:
        jatekosok (list): List of player usernames.
    """
    global jatek_instance
    jatek_instance = jatek([Jatekos(felhasznalo) for felhasznalo in jatekosok])

    db = get_db_session()
    username = session.get("username")
    user: Optional[User] = db.query(User).filter(User.username == username).first()

    game = Game(room_id=user.current_room_id)
    db.add(game)
    db.commit()

    for kartya in jatek_instance.state.pakli:
        existing_card = db.query(Card).filter_by(name=kartya.nev).first()

        if not existing_card:
            card = Card(name=kartya.nev)
            db.add(card)

    for j in jatek_instance.state.jatekosok:
        player = Player(name=j.nev, allitas=j.allitas)
        db.add(player)

        for kartya in j.kezbenlevo_kartyak:
            card = db.query(Card).filter_by(name=kartya.nev).first()
            if card:
                player.kezben_levo_lapok.append(card)

    db.commit()

    aktiv_nev = jatek_instance.state.aktiv_jatekos.nev

    jatekos_adatok = {}
    for j in jatek_instance.state.jatekosok:
        print(j.elotte_levo_kartyak)
        jatekos_adatok[j.nev] = {
            "elotte_levo_kartyak": j.elotte_levo_kartyak,
            "jatekos_kartyaszam": len(j.kezbenlevo_kartyak),
        }

    for j in jatek_instance.state.jatekosok:
        player_sid = socketek[j.nev]
        if player_sid:
            kezbenlevo_kartyak = [k.nev for k in j.kezbenlevo_kartyak]
            emit(
                "jatekos_adatok",
                {
                    "nev": j.nev,
                    "kezbenlevo_kartyak": kezbenlevo_kartyak,
                    "kezdo_jatekos": aktiv_nev,
                    "jatekos_adatok": jatekos_adatok,
                },
                to=player_sid,
            )
        print("kezbenlevo_kartyak", kezbenlevo_kartyak)


if __name__ == "__main__":
    reset_database()
    socketio.run(app, debug=True, host="0.0.0.0")
