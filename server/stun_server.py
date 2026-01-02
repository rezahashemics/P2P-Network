from flask import Flask, request, jsonify
import threading
import os
import redis

app = Flask(__name__)

redis_host = os.getenv('REDIS_HOST')
if redis_host:
    r = redis.Redis(host=redis_host, port=6379, db=0)
    use_redis = True
else:
    use_redis = False
    peers = {}  # Fallback to in-memory

def get_peers():
    if use_redis:
        return r.keys()
    else:
        return list(peers.keys())

def set_peer(username, data):
    if use_redis:
        r.hset(username, mapping=data)
    else:
        peers[username] = data

def get_peer(username):
    if use_redis:
        return r.hgetall(username)
    else:
        return peers.get(username)

def peer_exists(username):
    if use_redis:
        return r.exists(username)
    else:
        return username in peers

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    ip = data.get('ip')
    port = data.get('port')
    
    if not username or not ip or not port:
        return jsonify({'error': 'Missing fields'}), 400
    
    if peer_exists(username):
        return jsonify({'error': 'Username already exists'}), 409
    
    set_peer(username, {'ip': ip, 'port': port})
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/peers', methods=['GET'])
def get_peers_list():
    peer_list = get_peers()
    if use_redis:
        peer_list = [p.decode() for p in peer_list]
    return jsonify({'peers': peer_list}), 200

@app.route('/peerinfo', methods=['GET'])
def get_peer_info():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Missing username'}), 400
    
    info = get_peer(username)
    if not info:
        return jsonify({'error': 'Peer not found'}), 404
    
    if use_redis:
        info = {k.decode(): v.decode() for k, v in info.items()}
    
    return jsonify(info), 200

def run_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
