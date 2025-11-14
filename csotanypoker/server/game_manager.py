import os
import uuid
import json
from typing import List, Optional, Dict

from sqlalchemy.orm import Session
from csotanypoker.models.animal import Animal
from csotanypoker.models.player import VisiblePlayer, OpponentPlayer
from csotanypoker.server.game_background import GameLogic
from csotanypoker.models.clientgamestate import ClientGameState
from csotanypoker.server.gamestate import GameState
from csotanypoker.models.user import AI_NAMES, is_ai_player, this_is_ai_name
from csotanypoker.server.database import DBUser, DBGame


class GameManager:
    def __init__(self, socketio, sockets: dict, room_manager):
        self.socketio = socketio
        self.sockets = sockets
        self.room_manager = room_manager
        self.game_instances: Dict[str, GameLogic] = {}
        data_dir = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", ".")
        self.saves_dir = os.path.join(data_dir, "games_saves")
        os.makedirs(self.saves_dir, exist_ok=True)

    def get_game_instance(self, room_id: str) -> Optional[GameLogic]:
        return self.game_instances.get(room_id)

    def load_existing_games(self, db: Session) -> None:
        try:
            running_games = db.query(DBGame).filter(DBGame.game_status == "run").all()

            for db_game in running_games:
                try:
                    save_path = os.path.join(
                        self.saves_dir, f"game_{db_game.game_id}.pkl"
                    )
                    if not os.path.exists(save_path):
                        continue

                    loaded_state = GameState.load_from_file(save_path)

                    if loaded_state:
                        db_players = db_game.players
                        players = []
                        for db_player in db_players:
                            loaded_player = None
                            for p in loaded_state.players:
                                if p.username == db_player.username:
                                    loaded_player = p
                                    break

                            if loaded_player:
                                players.append(loaded_player)
                            else:
                                players.append(
                                    VisiblePlayer(username=db_player.username)
                                )

                        game_logic = GameLogic(
                            db_game.game_id,
                            players,
                            room_id=db_game.room_id,
                            from_db=True,
                        )

                        self.game_instances[db_game.room_id] = game_logic

                except Exception as game_error:
                    print(
                        f"Hiba a játék betöltése során ({db_game.game_id}): {game_error}"
                    )

        except Exception as e:
            print(f"Hiba a játékok betöltése során: {e}")

    def start_game(
        self, db: Session, players: List[str], room_id: str, reconnect: bool = False
    ) -> None:
        db_room = self.room_manager.get_room_by_id(db, room_id)
        if not db_room:
            return

        if reconnect:
            if room_id in self.game_instances:
                game_instance = self.game_instances[room_id]
                self.send_game_state_to_players(
                    db, game_instance, room_id, hide_card_for_unvisited=True
                )
            else:
                try:
                    existing_game = None
                    for game in db_room.games:
                        if game.game_status == "run":
                            existing_game = game
                            break

                    if existing_game:
                        save_path = f"csotanypoker/server/games_saves/game_{existing_game.game_id}.pkl"
                        loaded_state = GameState.load_from_file(save_path)

                        if loaded_state:
                            game_logic = GameLogic(
                                existing_game.game_id,
                                list(loaded_state.players),
                                room_id=room_id,
                            )
                            game_logic.state = loaded_state
                            self.game_instances[room_id] = game_logic

                            self.send_game_state_to_players(
                                db, game_logic, room_id, hide_card_for_unvisited=True
                            )
                        else:
                            print(f"Failed to load game state, creating new game")
                            reconnect = False
                except Exception as e:
                    print(f"Error during reconnect: {e}")
                    reconnect = False

            if reconnect:
                return

        if not reconnect:
            existing_game = None
            for game in db_room.games:
                if game.game_status == "run":
                    existing_game = game
                    break

            if existing_game:
                return

            unique_game_id = str(uuid.uuid4())

            try:
                self.game_instances[str(room_id)] = GameLogic(
                    id=unique_game_id,
                    players=[
                        VisiblePlayer(username=str(username)) for username in players
                    ],
                    room_id=room_id,
                )
                game_instance = self.game_instances[room_id]
                db_game = DBGame(
                    game_id=unique_game_id,
                    game_status="run",
                    loser_username=None,
                    room_id=room_id,
                )
                db.add(db_game)
                db.commit()
                for username in players:
                    db_user = (
                        db.query(DBUser).filter(DBUser.username == username).first()
                    )
                    if db_user:
                        db_game.players.append(db_user)

                db.commit()

                self.send_game_state_to_players(
                    db, game_instance, room_id, hide_card_for_unvisited=False
                )
                self.ai_activity(db, game_instance, room_id)

            except Exception as e:
                print(f"Error creating new game: {e}")

    def game_end(self, db: Session, room_id: str) -> None:
        room = self.room_manager.get_room_by_id(db, room_id)
        if not room:
            return

        game_instance = self.get_game_instance(room_id)
        if not game_instance:
            return

        loser_name = game_instance.state.active_player.username

        running_game = None
        for game in room.games:
            if game.game_status == "run":
                running_game = game
                break

        if running_game:
            running_game.loser_username = loser_name
            running_game.game_status = "end"
        else:
            print(f"Warning: No running game found in room {room_id}")

        db.commit()

        self.socketio.emit(
            "game_over",
            {"losing_player": loser_name},
            room=room_id,
        )

    def send_game_state_to_players(
        self,
        db: Session,
        game_instance,
        room_id: str,
        hide_card_for_unvisited: bool = True,
        nextplayer=None,
    ):
        try:
            active_users = (
                db.query(DBUser)
                .filter(DBUser.current_room_id == room_id, DBUser.is_active == True)
                .all()
            )
            active_usernames = {user.username for user in active_users}
            for player in game_instance.state.players:
                if player.username in active_usernames:
                    player_sid = self.sockets.get(player.username)
                    if is_ai_player(player.username):
                        continue
                    else:
                        if player_sid:
                            self._send_game_state_to_single_player(
                                game_instance,
                                player,
                                player_sid,
                                hide_card_for_unvisited,
                                nextplayer=nextplayer,
                            )
                        else:
                            print(f"No socket ID found for player: {player.username}")

        except Exception as e:
            print(f"Error in send_game_state_to_players: {e}")

    def _send_game_state_to_single_player(
        self,
        game_instance,
        player,
        player_sid,
        hide_card_for_unvisited: bool,
        nextplayer=None,
    ):
        try:
           
            client_game_state = self._build_client_game_state(game_instance)
           
            if (
                hide_card_for_unvisited
                and game_instance.state.question_card
                and player.username not in game_instance.state.visited_already
                and game_instance.state.targeted_player is not None
            ):
                client_game_state["question_card"] = "card_back"
            visible_player_data = self._build_visible_player_data(player)
            opponent_players_data = [
                self._build_opponent_player_data(p)
                for p in game_instance.state.players
                if p.username != player.username
            ]
            payload = {
                "game_state": client_game_state,
                "visible_player_data": visible_player_data,
                "opponent_players_data": opponent_players_data,
                "card_placed": str(nextplayer.username) if nextplayer else None,
            }

            try:
                json.dumps(payload)
            except (TypeError, ValueError) as e:
                print(f"JSON serialization error for {player.username}: {e}")
                return

            self.socketio.emit("Game_state", payload, to=player_sid)

        except Exception as e:
            print(f"Error sending game state to {player.username}: {e}")

    def _build_client_game_state(self, game_instance) -> dict:
        return ClientGameState(
            game_id=game_instance.state.game_id,
            room_id=game_instance.state.room_id,
            visited_already=game_instance.state.visited_already,
            voters=game_instance.state.voters,
            active_player_name=game_instance.state.active_player.username,
            targeted_player_name=game_instance.state.targeted_player.username
            if game_instance.state.targeted_player
            else None,
            question_card=game_instance.state.question_card,
            passing=game_instance.state.passing,
        ).model_dump()

    def _build_visible_player_data(self, player_data) -> dict:
        return player_data.model_dump(mode="json")

    def _build_opponent_player_data(self, player_data) -> dict:
        return OpponentPlayer(
            username=player_data.username,
            cards_in_front=player_data.cards_in_front,
            statement=player_data.statement,
            is_true=player_data.is_true,
            card_count_int=len(player_data.cards_in_hand),
        ).model_dump(mode="json")

    def handle_oke_click(
        self, db: Session, username: str, room_id: str, data: dict
    ) -> None:
        try:
            game_instance = self.get_game_instance(room_id)
            if not game_instance:
                return
            print("A jelenlegi kártya:", game_instance.state.question_card)
            
            client_game_state = data.get("game_state", {})
            statement = data.get("statement", None)
            for card in Animal:
                if card.value == client_game_state["question_card"]:
                    if game_instance.state.question_card is None:
                        game_instance.select_card(card, game_instance.state.passing)

            game_instance.select_target_player(
                client_game_state["targeted_player_name"]
            )

            if (
                game_instance.state.active_player.username
                not in game_instance.state.visited_already
            ):
                game_instance.state.visited_already.add(
                    game_instance.state.active_player.username
                )

            if (
                "active_player_name" in client_game_state
                and client_game_state["active_player_name"]
            ):
                active_player_name = client_game_state["active_player_name"]
                for player in game_instance.state.players:
                    if player.username == active_player_name:
                        game_instance.state.active_player = player
                        break

            statement_enum = None
            if statement:
                for card in Animal:
                    if card.value == statement:
                        statement_enum = card
                        break

            game_instance.make_statement(statement_enum)

            self.send_game_state_to_players(
                db, game_instance, room_id, hide_card_for_unvisited=True
            )

            if is_ai_player(game_instance.state.targeted_player.username):
                self.ai_guess(db, game_instance, room_id)

        except Exception as e:
            print(f"Error in handle_oke_click: {e}")

    def _process_guess(self, db: Session, game_instance, room_id: str, guess: bool):
        try:
            was_truthful, nextplayer = game_instance.state.ai_player.evaluate_guess(
                game_instance, guess
            )

            game_instance.state.visited_already = set(
                player.username for player in game_instance.state.players
            )
            self.send_game_state_to_players(
                db,
                game_instance,
                room_id,
                hide_card_for_unvisited=True,
                nextplayer=nextplayer,
            )

            self.socketio.start_background_task(
                target=lambda: (
                    self.socketio.sleep(4),
                    self._reset_callback(db, nextplayer, game_instance, room_id),
                )
            )

        except Exception as e:
            print(f"Error in _process_guess: {e}")

    def _check_and_handle_game_end(
        self, db: Session, game_instance, room_id: str
    ) -> bool:
        if game_instance.has_cards_in_hand():
            self.game_end(db, room_id)
            return True

        if game_instance.has_4_cards_in_front():
            self.game_end(db, room_id)
            return True

        return False

    def _reset_callback(self, db: Session, nextplayer, game_instance, room_id: str):
        game_instance.state.ai_player.reset_round(game_instance.state.players)
        game_instance.state.active_player = nextplayer

        if self._check_and_handle_game_end(db, game_instance, room_id):
            return

        game_instance.state.question_card = None
        game_instance.state.targeted_player = None
        game_instance.state.visited_already = set()
        game_instance.state.passing = False
        self.send_game_state_to_players(
            db, game_instance, room_id, hide_card_for_unvisited=True
        )
        self.ai_activity(db, game_instance, room_id)

    def ai_activity(
        self, db: Session, game_instance, room_id: str, passing: bool = False
    ):
        if not game_instance.state.active_player:
            return

        active_player_name = game_instance.state.active_player.username

        if not is_ai_player(
            active_player_name
        ) or not self.room_manager.all_players_active_in_room(room_id):
            return

        try:
            active_player = game_instance.state.active_player

            opponent_player_data = [
                OpponentPlayer(
                    username=p.username,
                    cards_in_front=p.cards_in_front,
                    statement=p.statement,
                    is_true=p.is_true,
                    card_count_int=len(p.cards_in_hand),
                )
                for p in game_instance.state.players
                if p.username != active_player.username
            ]

            selected_card, target_player_name, statement = (
                game_instance.state.ai_player.select_card_and_target(
                    opponent_player_data,
                    game_instance.state.question_card,
                    game_instance.state.visited_already,
                    active_player,
                    passing,
                )
            )

            if selected_card is None or target_player_name is None:
                if passing:
                    self.ai_guess(db, game_instance, room_id)
                return

            ai_game_state = {
                "question_card": selected_card.value,
                "targeted_player_name": target_player_name,
                "active_player_name": game_instance.state.active_player.username,
            }

            self.socketio.start_background_task(
                lambda: (
                    self.socketio.sleep(4.0),
                    self._execute_ai_move(
                        db, game_instance, ai_game_state, statement, passing
                    ),
                )
            )

        except Exception as e:
            print(f"Error in ai_activity: {e}")

    def _execute_ai_move(
        self,
        db: Session,
        game_instance,
        ai_game_state: dict,
        statement: Animal,
        passing: bool,
    ):
        room_id = game_instance.state.room_id
        if not self.room_manager.all_players_active_in_room(room_id):
            return

        self.socketio.sleep(1.0)

        self.handle_oke_click(
            db,
            game_instance.state.active_player.username,
            room_id,
            {
                "game_state": ai_game_state,
                "statement": statement,
                "pass": passing,
            },
        )

    def ai_handle_guess_internal(self, db, guess, game_instance, room_id):
        try:
            was_truthful, nextplayer = game_instance.state.ai_player.process_guess(
                game_instance, guess
            )

            game_instance.state.visited_already = set(
                player.username for player in game_instance.state.players
            )

            self.send_game_state_to_players(
                db, game_instance, room_id, hide_card_for_unvisited=True
            )
            self.socketio.start_background_task(
                target=lambda: (
                    self.socketio.sleep(4),
                    self._reset_callback(db, nextplayer, game_instance, room_id),
                )
            )

        except Exception as e:
            print(f"Error in ai_handle_guess_internal: {e}")

    def ai_guess(self, db: Session, game_instance, room_id: str):
        if not self.room_manager.all_players_active_in_room(room_id):
            return

        choice = game_instance.state.ai_player.decide_guess(game_instance)

        if choice == "pass":
            self.ai_pass_internal(db, game_instance, room_id)
            return

        tipp = choice == "true"
        self.socketio.sleep(4.0)
        self._process_guess(db, game_instance, room_id, tipp)

    def ai_pass_internal(self, db: Session, game_instance, room_id: str):
        game_instance.state.passing = True
        self.send_game_state_to_players(
            db,
            game_instance,
            room_id,
            hide_card_for_unvisited=True,
        )

        if game_instance.state.targeted_player is not None:
            next_player = game_instance.state.targeted_player
            game_instance.state.active_player = next_player
            game_instance.state.targeted_player = None

        if self._check_and_handle_game_end(db, game_instance, room_id):
            return
        self.socketio.sleep(4.0)
        self.send_game_state_to_players(
            db, game_instance, room_id, hide_card_for_unvisited=False
        )

        if self.room_manager.all_players_active_in_room(room_id):
            active_player_name = game_instance.state.active_player.username
            if is_ai_player(active_player_name):
                self.ai_activity(db, game_instance, room_id, passing=True)

    def resume_ai_activity_if_needed(self, db: Session, room_id: str):
        game_instance = self.get_game_instance(room_id)
        if not game_instance or not game_instance.state.active_player:
            return

        active_player_name = game_instance.state.active_player.username

        if is_ai_player(
            active_player_name
        ) and self.room_manager.all_players_active_in_room(room_id):
            has_question_card = game_instance.state.question_card is not None
            has_targeted_player = game_instance.state.targeted_player is not None

            if has_question_card and has_targeted_player:
                targeted_player_name = game_instance.state.targeted_player.username
                if is_ai_player(targeted_player_name):
                    self.ai_guess(db, game_instance, room_id)
                    return

            elif has_question_card and not has_targeted_player:
                self.ai_pass_internal(db, game_instance, room_id)
                return

            elif not has_question_card:
                print(
                    f"Resuming AI activity for {active_player_name} - no active round"
                )
                self.ai_activity(db, game_instance, room_id)
