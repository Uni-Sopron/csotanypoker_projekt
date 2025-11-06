from typing import Optional

from csotanypoker.models.user import AI_NAMES, is_ai_player, this_is_ai_name
from csotanypoker.server.database import DBUser, create_tables, get_db_session


def get_user_room_id(username: str) -> Optional[str]:
    with get_db_session() as db:
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        return db_user.current_room_id if db_user else None


def initialize_server_data(game_manager):
    create_tables()
    game_manager.load_existing_games(get_db_session())
    cleanup_inactive_users()


def cleanup_inactive_users():
    with get_db_session() as db:
        try:
            active_users = db.query(DBUser).filter(DBUser.is_active).all()
            inactive_count = 0

            for user in active_users:
                if not is_ai_player(user.username):
                    user.is_active = False
                    inactive_count += 1

            db.commit()
        except Exception as e:
            print(f"Hiba a felhasználók tisztítása során: {e}")
