import socket
import threading
import requests
import sys
import select

STUN_SERVER = 'http://stun_server:5000'
class Peer:
    def __init__(self, username, listen_port):
        self.username = username
        self.listen_port = listen_port
        self.connections = {}  # username -> socket
        self.tcp_server = None
        
        # Get local IP
        self.local_ip = socket.gethostbyname(socket.gethostname())
        
        # Register with STUN server
        self.register()

    def register(self):
        data = {
            'username': self.username,
            'ip': self.local_ip,
            'port': self.listen_port
        }
        try:
            response = requests.post(f'{STUN_SERVER}/register', json=data)
            if response.status_code == 201:
                print(f'Registered as {self.username} at {self.local_ip}:{self.listen_port}')
            else:
                print(f'Registration failed: {response.json()["error"]}')
                sys.exit(1)
        except Exception as e:
            print(f'Error registering: {e}')
            sys.exit(1)

    def start_tcp_server(self):
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.bind((self.local_ip, self.listen_port))
        self.tcp_server.listen(5)
        print(f'Listening for connections on {self.local_ip}:{self.listen_port}')
        
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while True:
            try:
                client_sock, addr = self.tcp_server.accept()
                print(f'Incoming connection from {addr}')
                threading.Thread(target=self.handle_incoming_connection, args=(client_sock, addr), daemon=True).start()
            except Exception as e:
                print(f'Error accepting connection: {e}')

    def handle_incoming_connection(self, sock, addr):
        # Receive connection request (simple protocol: first message is "CONNECT username")
        try:
            data = sock.recv(1024).decode()
            if data.startswith('CONNECT '):
                requester_username = data.split(' ')[1]
                print(f'{requester_username} wants to connect. Accept? (y/n)')
                accept = input().lower() == 'y'
                if accept:
                    sock.send(b'ACCEPTED')
                    self.connections[requester_username] = sock
                    print(f'Connected with {requester_username}')
                    threading.Thread(target=self.handle_chat, args=(sock, requester_username), daemon=True).start()
                else:
                    sock.send(b'REJECTED')
                    sock.close()
            else:
                sock.close()
        except Exception as e:
            print(f'Error handling connection: {e}')
            sock.close()

    def handle_chat(self, sock, username):
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    raise Exception('Connection closed')
                print(f'{username}: {data.decode()}')
            except Exception as e:
                print(f'Connection with {username} lost: {e}')
                sock.close()
                del self.connections[username]
                break

    def connect_to_peer(self, target_username):
        # Get peer info from STUN
        try:
            response = requests.get(f'{STUN_SERVER}/peerinfo?username={target_username}')
            if response.status_code == 200:
                info = response.json()
                ip = info['ip']
                port = int(info['port'])
            else:
                print(f'Failed to get peer info: {response.json()["error"]}')
                return
        except Exception as e:
            print(f'Error getting peer info: {e}')
            return
        
        # Connect via TCP
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(f'CONNECT {self.username}'.encode())
            response = sock.recv(1024).decode()
            if response == 'ACCEPTED':
                print(f'Connected to {target_username}')
                self.connections[target_username] = sock
                threading.Thread(target=self.handle_chat, args=(sock, target_username), daemon=True).start()
                return sock
            else:
                print('Connection rejected')
                sock.close()
        except Exception as e:
            print(f'Error connecting to {target_username}: {e}')

    def get_peer_list(self):
        try:
            response = requests.get(f'{STUN_SERVER}/peers')
            if response.status_code == 200:
                peers = response.json()['peers']
                peers = [p for p in peers if p != self.username]
                print('Available peers:', peers)
                return peers
            else:
                print('Failed to get peer list')
        except Exception as e:
            print(f'Error getting peer list: {e}')

    def send_message(self, target_username, message):
        if target_username in self.connections:
            sock = self.connections[target_username]
            try:
                sock.send(message.encode())
            except Exception as e:
                print(f'Error sending message: {e}')
                sock.close()
                del self.connections[target_username]
        else:
            print('Not connected to that peer')

    def run(self):
        self.start_tcp_server()
        
        print('Commands: list, connect <username>, send <username> <message>, exit')
        while True:
            inputs = [sys.stdin]
            readable, _, _ = select.select(inputs, [], [])
            for r in readable:
                if r == sys.stdin:
                    cmd = input().strip()
                    parts = cmd.split()
                    if parts[0] == 'list':
                        self.get_peer_list()
                    elif parts[0] == 'connect' and len(parts) == 2:
                        self.connect_to_peer(parts[1])
                    elif parts[0] == 'send' and len(parts) >= 3:
                        target = parts[1]
                        msg = ' '.join(parts[2:])
                        self.send_message(target, msg)
                    elif parts[0] == 'exit':
                        sys.exit(0)
                    else:
                        print('Invalid command')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python peer.py <username> <listen_port>')
        sys.exit(1)
    
    username = sys.argv[1]
    port = int(sys.argv[2])
    
    peer = Peer(username, port)
    peer.run()
