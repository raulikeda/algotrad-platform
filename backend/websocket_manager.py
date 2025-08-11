"""
WebSocket Connection Manager for Home Broker Simulator
"""

from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # User ID -> List of WebSocket connections
        self.user_connections: Dict[str, List[WebSocket]] = {}
        # WebSocket -> User ID mapping
        self.connection_users: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        
        self.user_connections[user_id].append(websocket)
        self.connection_users[websocket] = user_id
        
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            # Clean up empty user connection lists
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        if websocket in self.connection_users:
            del self.connection_users[websocket]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        if user_id not in self.user_connections:
            return
        
        connections = self.user_connections[user_id].copy()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                # Remove broken connection
                self.disconnect(websocket, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.user_connections.keys()):
            await self.send_to_user(user_id, message)
    
    async def broadcast_order_book(self, order_book: dict):
        """Broadcast order book update to all users"""
        await self.broadcast({
            "type": "order_book_update",
            "data": order_book
        })
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.user_connections.keys())
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.user_connections.values())
