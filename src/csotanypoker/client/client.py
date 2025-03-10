import threading
import socket
import json
import time
import pygame


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)



class Client:
    def __init__(self, host="127.0.0.1", port=55555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.rooms = []
        self.allapot=0
        pygame.init()
        self.width, self.height = 1400, 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Csotánypóker")
        self.font = pygame.font.Font(None, 50)
        self.font_kozepes = pygame.font.Font(None, 30)
        self.button_font = pygame.font.Font(None, 40)
        threading.Thread(target=self.receive).start()
        self.kezdo_oldal()

    def receive(self):
        while True:
            chunk = self.client.recv(1024).decode("ascii")
            if not chunk:
                break
            data = json.loads(chunk)
            self.uzenetek_kezelese(data)
    
    
    def uzenetek_kezelese(self, data):
        uzenet = data.get("type")

        if uzenet == "Szerver_csatlakozas":
            print(f">>>>>>>>>{data.get('message')}<<<<<<<<<<<")
            self.allapot=0
            
        elif uzenet == "Varakozas":
            print("Várakozás a játékosokra..")
            self.screen.fill(WHITE)
            self.allapot=4
            self.varo_oldal()
            time.sleep(1)
        elif uzenet == "szoba nevek":
            self.rooms = data.get("rooms", [])
         
        elif uzenet == "game_start":

            print(f"{data.get('message')}")
            kezben_levo_lapok = data.get("lapok", [])  
            print( kezben_levo_lapok)
            
            self.screen.fill(WHITE)
            self.allapot=5
            self.game_started_screen(kezben_levo_lapok)

            
    def send(self, message):
        data = json.dumps(message).encode("ascii")
        self.client.send(data)
        

    def name_input_screen(self):
        input_box = pygame.Rect(300, 250, 200, 50)
        button_rect = pygame.Rect(350, 320, 150, 50)
        input_text = ""
        
        while self.allapot == 0:
            self.screen.fill(WHITE)
            
            self.szoveg_felrajzolas("Add meg a neved:", (250, 180), self.font, BLACK)
            self.beviteli_mezo_felrajzolasa(input_box, input_text, True)
            self.gomb_felrajzolas("Belépés", button_rect, BLACK)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot =10
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.nev_elkuldese(input_text)
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        self.nev_elkuldese(input_text)
                        return

    def nev_elkuldese(self, input_text):
        print(f"Játékos neve: {input_text}")
        self.send({"type": "nev", "nev": input_text})
        self.allapot = 1
        self.kezdo_menu()

    def kezdo_oldal(self):
        button_rect = pygame.Rect(self.width // 2 - 50, self.height // 2 - 20, 100, 50)

        while self.allapot == 0:
            self.screen.fill(WHITE)
            
            self.szoveg_felrajzolas("Csotánypóker", (self.width // 2, self.height // 2 - 100), self.font, BLACK)
            self.gomb_felrajzolas("Start", button_rect, BLACK)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                    self.screen.fill(WHITE)
                    self.name_input_screen()
    def kezdo_menu(self):
        buttons = [
            ("Szoba készítés", (200, 150)),
            ("Csatlakozás szobához", (200, 250)),
            ("Random szobához csatlakozás", (200, 350)),
        ]
        button_rects = [pygame.Rect(x, y, 450, 50) for _, (x, y) in buttons]
        
        
        while self.allapot==1: 
            
            self.screen.fill(WHITE)
            self.szoveg_felrajzolas("Menü:", (self.screen.get_width() // 2, 50), self.font, BLACK)
            for idx, (text, (x, y)) in enumerate(buttons):
                
                self.gomb_felrajzolas(text, button_rects[idx])
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.allapot=10
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for idx, rect in enumerate(button_rects):
                        if rect.collidepoint(event.pos):
                            self.allapot=2
                            if idx == 0:  
                                self.screen.fill(WHITE)      
                                self.szobat_letrehozo_oldal()                                
                            elif idx == 1:  
                                self.csatalakozo_oldal()          
                            elif idx == 2:                                    
                                self.send({"type": "random_room", "message": "Csatlakozás véletlenszerű szobához..."})

    def szobat_letrehozo_oldal(self):
        szoba_neve_mezo = pygame.Rect(300, 150, 200, 40)
        jelszo_mezo = pygame.Rect(300, 250, 200, 40)
        max_jatekosok_mezo = pygame.Rect(300,350, 200, 40)

        szoba_neve_szoveg = ""
        jelszo_szoveg = ""
        max_jatekosok_szoveg = ""

        aktiv_bemenet = None  

        while self.allapot == 2:
            self.screen.fill(WHITE)
            self.szoveg_felrajzolas("Szoba létrehozása", (self.screen.get_width() // 2, 50), self.font)

            self.szoveg_felrajzolas("Szoba neve:", (300, 130), self.font)
            self.beviteli_mezo_felrajzolasa(szoba_neve_mezo, szoba_neve_szoveg, aktiv_bemenet == 'szoba_neve')

            self.szoveg_felrajzolas("Jelszó:", (300, 230), self.font)
            self.beviteli_mezo_felrajzolasa(jelszo_mezo, jelszo_szoveg, aktiv_bemenet == 'jelszo')

            self.szoveg_felrajzolas("Max. játékosok (2-6):", (300, 330), self.font)
            self.beviteli_mezo_felrajzolasa(max_jatekosok_mezo, max_jatekosok_szoveg, aktiv_bemenet == 'max_jatekosok')

            self.gomb_felrajzolas("Szoba létrehozása", pygame.Rect(350, 400, 300, 50))

            pygame.display.flip()

    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                    pygame.quit()
                    return

                elif event.type == pygame.MOUSEBUTTONDOWN:
                   
                    if szoba_neve_mezo.collidepoint(event.pos):
                        aktiv_bemenet = 'szoba_neve'
                    elif jelszo_mezo.collidepoint(event.pos):
                        aktiv_bemenet = 'jelszo'
                    elif max_jatekosok_mezo.collidepoint(event.pos):
                        aktiv_bemenet = 'max_jatekosok'
                    elif pygame.Rect(350, 400, 300, 50).collidepoint(event.pos):
                        
                        try:
                            max_jatekosok = int(max_jatekosok_szoveg)
                            if 2 <= max_jatekosok <= 6:
                                self.send({
                                    "type": "create_room",
                                    "room_name": szoba_neve_szoveg,
                                    "password": jelszo_szoveg,
                                    "max_players": max_jatekosok
                                })
                        except ValueError:
                            pass  # Hibás számbevitel 
                elif event.type == pygame.KEYDOWN:
                    if aktiv_bemenet == 'szoba_neve':
                        if event.key == pygame.K_BACKSPACE:
                            szoba_neve_szoveg = szoba_neve_szoveg[:-1]
                        else:
                            szoba_neve_szoveg += event.unicode
                    elif aktiv_bemenet == 'jelszo':
                        if event.key == pygame.K_BACKSPACE:
                            jelszo_szoveg = jelszo_szoveg[:-1]
                        else:
                            jelszo_szoveg += event.unicode
                    elif aktiv_bemenet == 'max_jatekosok':
                        if event.key == pygame.K_BACKSPACE:
                            max_jatekosok_szoveg = max_jatekosok_szoveg[:-1]
                        else:
                            if event.unicode.isdigit(): 
                                max_jatekosok_szoveg += event.unicode    
                        

    def jelszo_bekeres(self, uzenet):
        
        szoveg = ""
        
        aktiv = True

        while aktiv:
            self.screen.fill(WHITE)
          
            self.szoveg_felrajzolas(uzenet, (50, 200), self.font, BLACK)

            self.beviteli_mezo_felrajzolasa(pygame.Rect(50, 250, 300, 50), szoveg, True)
           
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return szoveg
                    elif event.key == pygame.K_BACKSPACE:
                        szoveg = szoveg[:-1]  
                    else:
                        szoveg += event.unicode
                


    def varo_oldal(self):
    
        
        text = self.font.render("Várakozunk a játékosokra...", True, BLACK)
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 100))
       
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.allapot = 10
                return  
        
        
    
                
        
       
        self.screen.fill(WHITE)
        
       
        self.screen.blit(text, text_rect)
        
    
        pygame.display.flip()
        

    def jelszo_bekeres(self, prompt):
       
        input_text = ""
        

        while self.allapot==3:
            self.screen.fill(WHITE)
            text_surface = self.font.render(prompt, True, BLACK)
            self.screen.blit(text_surface, (50, 200))

      
            input_rect = pygame.Rect(50, 250, 300, 50)
            pygame.draw.rect(self.screen, GRAY, input_rect)
            text_surface = self.font.render(input_text, True, BLACK)
            self.screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot=10
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return input_text 
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]  
                    else:
                        input_text += event.unicode  
    

    def csatalakozo_oldal(self):
       
        self.send({"type": "get_rooms"})
        
        while self.allapot==2:
             

            self.screen.fill(WHITE)
            title = self.font.render("Válassz egy szobát:", True, BLACK)
            self.screen.blit(title, (50, 30))

           
            room_buttons = []
            for i, room in enumerate(self.rooms):
                room_text = self.font.render(room, True, BLUE)
                rect = room_text.get_rect(topleft=(50, 100 + i * 50))
                room_buttons.append((rect, room)) 
                self.screen.blit(room_text, rect.topleft)

            pygame.display.flip()

           
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot=10
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for rect, room in room_buttons:
                        if rect.collidepoint(mouse_pos):
                            self.allapot=3
                            password = self.jelszo_bekeres(f"{room} jelszava:")  
                            self.send({"type": "join_room", "room_name": room, "password": password})
                        
        
    def game_started_screen(self,kezben_levo_lapok):
       
        small_font = pygame.font.Font(None, 20)  
        sor_hossz = 5  

        while self.allapot == 5:
            self.screen.fill(WHITE)

            
            text = self.font.render("A játék elkezdődött!", True, BLACK)
            self.screen.blit(text, (200, 50))

            
            x_start, y_start = 50, 100 
            x, y = x_start, y_start
            spacing = 100  

            for i, lap in enumerate(kezben_levo_lapok):
                lap_text = small_font.render(str(lap), True, BLACK)
                self.screen.blit(lap_text, (x, y))

                x += spacing  
                if (i + 1) % sor_hossz == 0:  
                    x = x_start
                    y += 40  

            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.allapot = 10

            pygame.display.flip()


    def szoveg_felrajzolas(self, text, position, font, color=BLACK):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)  
        self.screen.blit(text_surface, text_rect)


    def beviteli_mezo_felrajzolasa(self, rect, text, active=False):
        color = BLACK if active else GRAY
        pygame.draw.rect(self.screen, color, rect, 2)
        input_surface = self.font_kozepes.render(text, True, BLACK)
        self.screen.blit(input_surface, (rect.x + 10, rect.y + 10))


    def gomb_felrajzolas(self, text, rect, color=BLACK):
        pygame.draw.rect(self.screen, color, rect)
        button_text = self.button_font.render(text, True, WHITE)
        self.screen.blit(button_text, (rect.x + 25, rect.y + 10))

def main():
    client = Client()
    

if __name__ == "__main__":
    main()
