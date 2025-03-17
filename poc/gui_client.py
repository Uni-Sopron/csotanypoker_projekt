import pygame
import pygame.font
import socketio
import threading


pygame.init()
WIDTH, HEIGHT = 1400, 750
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
MESSAGE_HEIGHT = HEIGHT - 100
INPUT_Y = HEIGHT - 70


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chat")  # ablak címe
font = pygame.font.Font(None, 30)


sio = socketio.Client()
connected = False
username = ""
messages = []
message_surface = pygame.Surface((WIDTH, MESSAGE_HEIGHT)) # üzenetek megjelenítésére szolgáló felület
input_text = "" 
connection_event = threading.Event()

@sio.event
def connect():
    global connected
    connected = True
    sio.emit("register", username)
    connection_event.set()

@sio.event
def message(data):
    messages.append(data)
    update_message_display()

@sio.event
def disconnect():
    global connected
    connected = False
    connection_event.clear()




def update_message_display():
    message_surface.fill(WHITE) # képernyő törlése
    text_y_position = 10 
    for msg in messages[-20:]:  
        words = msg.split(' ')
        line = ""
        for word in words:
            test_line = line + word + " "
            if font.size(test_line)[0] < WIDTH - 20:
                line = test_line
            else:
                message_surface.blit(font.render(line, True, BLACK), (10, text_y_position ))
                text_y_position  += font.size(line)[1] + 5
                line = word + " "
        if line:
            message_surface.blit(font.render(line, True, BLACK), (10, text_y_position ))
            text_y_position += font.size(line)[1] + 10
def connect_to_server():
    sio.connect("http://localhost:5555")
    

def login_screen():
    global username
    input_box = pygame.Rect(WIDTH // 4, HEIGHT // 2, WIDTH // 2, 50)
    text = ''
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and text:
                    username = text
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

        screen.fill(WHITE)
        title = font.render("Add meg a neved ", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        pygame.draw.rect(screen, GRAY, input_box)
        txt = font.render(text, True, BLACK)
        screen.blit(txt, (input_box.x + 5, input_box.y + 15))
        pygame.display.flip()
       

def waiting_screen():
    while not connection_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        screen.fill(WHITE)
        text = font.render("Kapcsolódás a szerverhez...", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
    return True

def main():
    global input_text
    if not login_screen():
        return

    connection_event.clear()
    threading.Thread(target=connect_to_server, daemon=True).start()
    if not waiting_screen():
        return

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text and connected:
                        sio.send(input_text)
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        if not connected and not waiting_screen():
            break

        screen.blit(message_surface, (0, 0))
        pygame.draw.rect(screen, GRAY, (10, INPUT_Y, WIDTH - 30, 40))
        if input_text:
            txt = font.render(input_text, True, BLACK)
            screen.blit(txt, (20, INPUT_Y + 12))
        
        pygame.display.flip()
        
    if connected:
        sio.disconnect()
    pygame.quit()

if __name__ == "__main__":
    main()