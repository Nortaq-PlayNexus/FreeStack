"""
WebSocket server for FreeStack.

Provides real-time communication with rooms, presence, and auth.
"""

import asyncio
import json
import signal
from typing import Any, Dict, List, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol

from ...core.config import settings
from ...core.auth import verify_token
from ...core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class Connection:
    """WebSocket connection wrapper."""

    def __init__(self, websocket: WebSocketServerProtocol, user_id: str, user_email: str):
        self.websocket = websocket
        self.user_id = user_id
        self.user_email = user_email
        self.rooms: Set[str] = set()
        self.metadata: Dict[str, Any] = {}

    async def send(self, message: Dict[str, Any]) -> None:
        """Send a message to this connection."""
        await self.websocket.send(json.dumps(message))

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the connection."""
        await self.websocket.close(code, reason)


class Room:
    """WebSocket room for broadcasting."""

    def __init__(self, name: str):
        self.name = name
        self.connections: Set[Connection] = set()

    def add(self, connection: Connection) -> None:
        """Add a connection to the room."""
        self.connections.add(connection)
        connection.rooms.add(self.name)

    def remove(self, connection: Connection) -> None:
        """Remove a connection from the room."""
        self.connections.discard(connection)
        connection.rooms.discard(self.name)

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Connection] = None) -> None:
        """Broadcast a message to all connections in the room."""
        disconnected = set()
        for connection in self.connections:
            if connection == exclude:
                continue
            try:
                await connection.send(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.remove(conn)


class WebSocketManager:
    """Manages WebSocket connections and rooms."""

    def __init__(self):
        self.connections: Dict[str, Connection] = {}
        self.rooms: Dict[str, Room] = {}
        self.user_connections: Dict[str, Set[Connection]] = {}

    def get_room(self, name: str) -> Room:
        """Get or create a room."""
        if name not in self.rooms:
            self.rooms[name] = Room(name)
        return self.rooms[name]

    def add_connection(self, connection: Connection) -> None:
        """Register a new connection."""
        self.connections[connection.websocket.id] = connection

        if connection.user_id not in self.user_connections:
            self.user_connections[connection.user_id] = set()
        self.user_connections[connection.user_id].add(connection)

    def remove_connection(self, connection: Connection) -> None:
        """Unregister a connection."""
        self.connections.pop(connection.websocket.id, None)

        user_conns = self.user_connections.get(connection.user_id, set())
        user_conns.discard(connection)
        if not user_conns:
            self.user_connections.pop(connection.user_id, None)

        # Remove from all rooms
        for room_name in list(connection.rooms):
            room = self.rooms.get(room_name)
            if room:
                room.remove(connection)

    async def handle_message(self, connection: Connection, message: Dict[str, Any]) -> None:
        """Handle incoming message."""
        msg_type = message.get("type")

        if msg_type == "join":
            await self.handle_join(connection, message)
        elif msg_type == "leave":
            await self.handle_leave(connection, message)
        elif msg_type == "message":
            await self.handle_room_message(connection, message)
        elif msg_type == "ping":
            await connection.send({"type": "pong"})
        else:
            logger.warning("Unknown message type", type=msg_type)

    async def handle_join(self, connection: Connection, message: Dict[str, Any]) -> None:
        """Handle join room request."""
        room_name = message.get("room")
        if not room_name:
            await connection.send({"type": "error", "message": "Room name required"})
            return

        room = self.get_room(room_name)
        room.add(connection)

        await connection.send({
            "type": "joined",
            "room": room_name,
            "users": [c.user_email for c in room.connections],
        })

        # Notify others
        await room.broadcast({
            "type": "user_joined",
            "room": room_name,
            "user": connection.user_email,
        }, exclude=connection)

        logger.info("User joined room", user=connection.user_email, room=room_name)

    async def handle_leave(self, connection: Connection, message: Dict[str, Any]) -> None:
        """Handle leave room request."""
        room_name = message.get("room")
        if not room_name:
            return

        room = self.rooms.get(room_name)
        if room:
            room.remove(connection)

            await room.broadcast({
                "type": "user_left",
                "room": room_name,
                "user": connection.user_email,
            })

        await connection.send({"type": "left", "room": room_name})
        logger.info("User left room", user=connection.user_email, room=room_name)

    async def handle_room_message(self, connection: Connection, message: Dict[str, Any]) -> None:
        """Handle room message."""
        room_name = message.get("room")
        content = message.get("content")

        if not room_name or content is None:
            await connection.send({"type": "error", "message": "Room and content required"})
            return

        room = self.rooms.get(room_name)
        if not room or connection not in room.connections:
            await connection.send({"type": "error", "message": "Not in room"})
            return

        await room.broadcast({
            "type": "message",
            "room": room_name,
            "user": connection.user_email,
            "content": content,
        }, exclude=connection)

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Send a message to all connections of a user."""
        connections = self.user_connections.get(user_id, set())
        for connection in connections:
            try:
                await connection.send(message)
            except Exception:
                self.remove_connection(connection)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "total_rooms": len(self.rooms),
            "rooms": {
                name: len(room.connections)
                for name, room in self.rooms.items()
            },
        }


manager = WebSocketManager()


async def authenticate_websocket(websocket: WebSocketServerProtocol) -> Optional[Dict[str, str]]:
    """Authenticate WebSocket connection."""
    # Get token from query params or first message
    query_params = dict(param.split("=") for param in websocket.request_headers.get("sec-websocket-protocol", "").split(";") if "=" in param)

    # Try token from query string
    token = query_params.get("token")
    if not token:
        # Wait for first message with token
        try:
            first_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(first_message)
            token = data.get("token")
        except Exception:
            return None

    if not token:
        return None

    # Verify token
    payload = verify_token(token)
    if not payload:
        return None

    return {
        "user_id": payload.sub,
        "email": payload.email,
    }


async def handle_connection(websocket: WebSocketServerProtocol) -> None:
    """Handle a WebSocket connection."""
    # Authenticate
    auth = await authenticate_websocket(websocket)
    if not auth:
        await websocket.close(4001, "Authentication required")
        return

    # Create connection
    connection = Connection(websocket, auth["user_id"], auth["email"])
    manager.add_connection(connection)

    logger.info("WebSocket connected", user=connection.user_email, connection_id=websocket.id)

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await manager.handle_message(connection, data)
            except json.JSONDecodeError:
                await connection.send({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.exception("Error handling message", error=str(e))
                await connection.send({"type": "error", "message": "Internal error"})
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.exception("Connection error", error=str(e))
    finally:
        manager.remove_connection(connection)
        logger.info("WebSocket disconnected", user=connection.user_email, connection_id=websocket.id)


async def run_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8001,
) -> None:
    """Run the WebSocket server."""
    logger.info("Starting WebSocket server", host=host, port=port)

    server = await websockets.serve(
        handle_connection,
        host,
        port,
        ping_interval=settings.websocket.ping_interval,
        ping_timeout=settings.websocket.ping_timeout,
        max_size=settings.websocket.max_message_size,
        max_queue=settings.websocket.max_connections,
    )

    # Handle shutdown
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    await shutdown_event.wait()

    logger.info("Shutting down WebSocket server")
    server.close()
    await server.wait_closed()