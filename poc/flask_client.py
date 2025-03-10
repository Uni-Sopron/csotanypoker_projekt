import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("Kapcsolódva a szerverhez!")
    username = input("Add meg a neved: ")
    sio.emit("register", username)

@sio.event
def message(data):
    print(data)

@sio.event
def disconnect():
    print("Kapcsolat bontva.")

def start_client():
    sio.connect("http://localhost:5555") 
    while True:
        msg = input()
        if msg.lower() == "exit":
            sio.disconnect()
            break
        sio.send(msg)  

if __name__ == "__main__":
    start_client()
