import pygame
import socketio
import threading
from typing import Optional, List, Tuple

pygame.init()  # Initializing Pygame
# Window configuration
WIDTH: int = 1400
HEIGHT: int = 750
WHITE: Tuple[int, int, int] = (255, 255, 255)
BLACK: Tuple[int, int, int] = (0, 0, 0)
GRAY: Tuple[int, int, int] = (200, 200, 200)
RED: Tuple[int, int, int] = (255, 0, 0)
MESSAGE_HEIGHT: float = HEIGHT - 100
INPUT_Y: float = HEIGHT - 70

# Window creation
screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chat")  # Window title
font: pygame.font.Font = pygame.font.Font(None, 30)

# SocketIO client configuration
sio: socketio.Client = socketio.Client()
connected: bool = False
username: str = ""
messages: List[str] = []  # List of messages
message_surface: pygame.Surface = pygame.Surface(
    (int(WIDTH), int(MESSAGE_HEIGHT))
)  # Surface for displaying messages
input_text: str = ""
connection_event: threading.Event = threading.Event()
username_accepted: Optional[bool] = None


# SocketIO event handlers
@sio.event
def connect() -> None:
    """
    Connection event handling
    """
    global connected
    connected = True
    connection_event.set()


@sio.event
def message(data: str) -> None:
    """
    It saves the messages received from the server and updates the screen.
    Args:
        data (str): The message text.
    """
    messages.append(data)
    update_message_display()


@sio.event
def disconnect() -> None:
    """
    Connection termination event handling
    """
    global connected
    connected = False
    connection_event.clear()


@sio.event
def register_response(success: bool) -> None:
    """
    If the server accepts the username, it sets the username_accepted variable to True.
    Otherwise, it sets it to False.
    Args:
        success (bool): Username acceptance status.
    """
    global username_accepted
    username_accepted = success


# Displaying messages on the screen
def update_message_display() -> None:
    """Displaying messages on the screen"""
    message_surface.fill(WHITE)
    text_y_position: int = 10
    for msg in messages[-20:]:  # A maximum of 20 messages will be displayed
        words: list = msg.split(" ")
        line: str = ""
        for word in words:
            test_line: str = line + word + " "
            if font.size(test_line)[0] < WIDTH - 20:  # If the line is not too wide
                line = test_line
            else:
                message_surface.blit(
                    font.render(line, True, BLACK), (10, text_y_position)
                )
                text_y_position += font.size(line)[1] + 5
                line = word + " "
        if line:
            message_surface.blit(font.render(line, True, BLACK), (10, text_y_position))
            text_y_position += font.size(line)[1] + 10


def connect_to_server() -> None:
    """
    Establishes the SocketIO connection with the server at the specified address.
    """
    sio.connect("http://localhost:5555")


def login_screen() -> bool:
    """
    Displays the login screen where it prompts for the username and sends it to the server.
    If the name is already taken, it asks for a new name.
    """
    global username, username_accepted
    input_box: pygame.Rect = pygame.Rect(WIDTH // 4, HEIGHT // 2, WIDTH // 2, 50)
    username: str = ""
    while not username_accepted:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # exit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username:
                    sio.emit("register", username)  # registering the username
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    username += event.unicode
        screen.fill(WHITE)
        title: pygame.Surface = font.render("Add meg a neved:", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        pygame.draw.rect(screen, GRAY, input_box)
        username_text: pygame.Surface = font.render(username, True, BLACK)
        screen.blit(username_text, (input_box.x + 5, input_box.y + 15))
        if username_accepted is False:
            error_message: pygame.Surface = font.render(
                "Ez a név foglalt, próbálj másikat!", True, RED
            )
            screen.blit(
                error_message,
                (WIDTH // 2 - error_message.get_width() // 2, HEIGHT // 2 + 40),
            )
        pygame.display.flip()
    return True


def waiting_screen() -> bool:
    """
    Displays the waiting message until the connection to the server is established.
    """
    while not connection_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        screen.fill(WHITE)
        text: pygame.Surface = font.render("Kapcsolódás a szerverhez...", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
    return True


def main() -> None:
    """The main program where the game runs"""
    global input_text

    threading.Thread(
        target=connect_to_server, daemon=True
    ).start()  # Server connection on a separate thread
    if not waiting_screen():
        return
    connection_event.wait()  # Waiting for connection
    if not login_screen():
        return

    running: bool = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_text and connected:
                    sio.send(input_text)  # Sending the message to the server
                    input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        # Displaying messages and input field
        screen.blit(message_surface, (0, 0))
        pygame.draw.rect(screen, GRAY, (10, INPUT_Y, WIDTH - 30, 40))
        if input_text:
            text: pygame.Surface = font.render(input_text, True, BLACK)
            screen.blit(text, (20, INPUT_Y + 12))

        pygame.display.flip()
    sio.disconnect()
    pygame.quit()  # Closing Pygame


if __name__ == "__main__":
    main()  # Running the main function
