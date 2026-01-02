# P2P Decentralized Chat System

A robust Peer-to-Peer (P2P) chat application utilizing a **STUN server** for peer discovery, **Redis** for state management, and **Docker** for network virtualization and isolation.

## 🏗 System Architecture

The project is divided into three main components:

1. **STUN Server (Flask)**: Acts as a directory service. It manages peer registrations, tracks active users, and provides connection metadata.
2. **Redis**: A high-performance key-value store used by the STUN server to persist peer information and ensure rapid lookups.
3. **Peer Nodes**: Python-based clients that register with the server and establish direct **TCP Socket** connections with other peers for real-time messaging.

## 📁 Project Structure

```text
.
├── docker-compose.yml       # Orchestrates STUN server and Redis
├── peer/
│   ├── Dockerfile           # Environment for peer instances
│   └── peer.py              # P2P logic (TCP Sockets & Discovery)
└── server/
    ├── Dockerfile           # Environment for STUN server
    └── stun_server.py       # Flask API & Redis integration

```

## 🚀 Getting Started

### Prerequisites

* Docker & Docker Compose
* Python 3.x (if running peers outside of Docker)

### 1. Start the Infrastructure

Launch the STUN server and Redis database:

```bash
docker compose up --build

```

The server will be available at `http://localhost:5000`. You can verify it's running by visiting `http://localhost:5000/peers` in your browser.

### 2. Launch Peer Nodes

In separate terminals, start multiple peers. Using the Docker network ensures they can communicate in an isolated environment.

**Peer 1 (User A):**

```bash
docker build -t peer-image ./peer
docker run -it --network p2p_network -p 8001:8001 peer-image python peer.py user1 8001

```

**Peer 2 (User B):**

```bash
docker run -it --network p2p_network -p 8002:8002 peer-image python peer.py user2 8002

```

## 💬 Usage Guide

Once a peer is running, you can use the following console commands:

| Command | Description |
| --- | --- |
| `list` | Fetch and display all available peers from the STUN server. |
| `connect <username>` | Send a connection request to a specific peer via TCP. |
| `send <username> <msg>` | Send a real-time message to a connected peer. |
| `exit` | Unregister from the server and close all connections. |

## 🛠 Features

* **Peer Discovery**: Dynamic registration and lookup using the STUN server.
* **Request/Accept Logic**: Peers must explicitly accept incoming connection requests before messaging begins.
* **Concurrency**: Uses Python's `threading` to handle multiple simultaneous peer connections without blocking.
* **Docker Isolation**: Each node runs in its own container, simulating a real-world distributed environment.
* **Persistence**: Redis ensures that peer data is managed efficiently on the server side.

## 🛡 Error Handling

* **Duplicate Users**: The server prevents two peers from registering with the same username.
* **Graceful Exit**: If a peer crashes or disconnects, the STUN server identifies the timeout, and connected peers are notified of the lost connection.
* **Input Validation**: Built-in checks for invalid commands or malformed messages.

---

**Developed by:** [Reza Hashemi](https://www.google.com/search?q=https://github.com/rezahashemics)

**Academic Year:** Fall 1404

