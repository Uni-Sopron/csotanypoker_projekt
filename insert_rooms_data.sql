
INSERT INTO
    rooms (
        room_id,
        name,
        max_player_count,
        password_protected,
        password
    )
VALUES (
        '926254321',
        'Valaki szobaja',
        4,
        0,
        NULL
    ),
    (
        '423156789',
        'Valaki szobaja',
        4,
        1,
        'defaultpassword'
    ),
    (
        '123456789',
        'Kerekasztal',
        6,
        0,
        NULL
    ),
    (
        '98765se4321',
        'Alma',
        3,
        1,
        'defaultpassword'
    ),
    (
        '1234sdf56789',
        'ELSO',
        6,
        0,
        NULL
    ),
    (
        '987654321',
        'ELSO',
        3,
        1,
        'defaultpassword'
    );


SELECT
    room_id,
    name,
    max_player_count,
    password_protected,
    (
        SELECT COUNT(*)
        FROM users
        WHERE
            current_room_id = rooms.room_id
    ) as current_player_count
FROM rooms;

SELECT u.username, u.current_room_id, r.name as room_name
FROM users u
    LEFT JOIN rooms r ON u.current_room_id = r.room_id
WHERE
    u.current_room_id IS NOT NULL;