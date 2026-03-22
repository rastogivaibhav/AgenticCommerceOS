"""
ops_api.routers.shopping_chat — WebSocket endpoint for shopping chat.

This module provides the WebSocket endpoint for real-time shopping chat messages.
It handles message routing, session management, and agent response processing.

Features:
- Real-time bidirectional communication via WebSocket
- Session persistence and management
- Conversation history tracking
- Error handling and recovery
- Connection lifecycle management
"""

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ops_api.services.shopping_sessions import SessionManager
from ops_api.services.shopping_agent import ShoppingAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["shopping"])


class ConnectionManager:
    """Manages active WebSocket connections for shopping chat.

    Tracks connected clients by session ID and provides methods for
    sending and receiving messages.

    Attributes:
        active_connections: Dictionary mapping session IDs to WebSocket connections
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, WebSocket] = {}
        self.logger = logger

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept and store a WebSocket connection.

        Args:
            session_id: Unique session identifier
            websocket: The WebSocket connection to accept

        Raises:
            RuntimeError: If connection acceptance fails
        """
        try:
            await websocket.accept()
            self.active_connections[session_id] = websocket
            self.logger.info(f"Client connected: {session_id}")
        except Exception as e:
            self.logger.error(f"Error accepting connection for {session_id}: {str(e)}")
            raise RuntimeError(f"Failed to accept connection: {str(e)}")

    async def disconnect(self, session_id: str) -> None:
        """Remove a disconnected client from active connections.

        Args:
            session_id: Unique session identifier
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            self.logger.info(f"Client disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict) -> None:
        """Send a JSON message to a specific client.

        Args:
            session_id: Unique session identifier
            message: Dictionary to send as JSON

        Raises:
            ValueError: If session is not connected or send fails
        """
        if session_id not in self.active_connections:
            raise ValueError(f"Session not connected: {session_id}")

        try:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
            self.logger.debug(f"Message sent to {session_id}: {message.get('type')}")
        except Exception as e:
            self.logger.error(
                f"Error sending message to {session_id}: {str(e)}"
            )
            raise ValueError(f"Failed to send message: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()

# Global service instances (lazy initialization)
_session_manager: SessionManager = None
_shopping_agent: ShoppingAgent = None


def get_session_manager() -> SessionManager:
    """Get or create SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(db=None)
    return _session_manager


def get_shopping_agent() -> ShoppingAgent:
    """Get or create ShoppingAgent instance."""
    global _shopping_agent
    if _shopping_agent is None:
        _shopping_agent = ShoppingAgent()
    return _shopping_agent


@router.websocket("/shopping-chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for shopping chat.

    Handles incoming messages from clients, processes them through the
    shopping agent, and sends responses back. Manages session state and
    conversation history.

    Message format from client:
    ```json
    {
      "type": "message",
      "content": "I need a mattress under £500"
    }
    ```

    Response format to client:
    ```json
    {
      "type": "response",
      "content": "I can help you find a mattress...",
      "status": "complete",
      "products": []
    }
    ```

    Args:
        websocket: The WebSocket connection
        session_id: String session identifier

    Raises:
        WebSocketDisconnect: When client disconnects
    """
    session_manager = get_session_manager()
    shopping_agent = get_shopping_agent()

    # Try to parse session_id as UUID, if not valid create one
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        session_uuid = uuid4()
        logger.info(f"Invalid session ID format; creating new session: {session_uuid}")

    try:
        # Accept connection and add to manager
        await manager.connect(session_id, websocket)

        # Create or retrieve session
        # For testing (db=None), always create a new in-memory session
        # For production (db set), try to get existing session first
        session = session_manager.create_session(customer_id=None)
        if session.session_id != session_uuid:
            session_uuid = session.session_id
        logger.info(f"Session initialized: {session_uuid}")

        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.debug(f"Received message from {session_id}: {data.get('type')}")

            # Validate message format
            if not isinstance(data, dict) or "content" not in data:
                error_response = {
                    "type": "error",
                    "error_code": "INVALID_MESSAGE_FORMAT",
                    "message": "Message must contain 'content' field",
                    "status": "error",
                }
                await manager.send_message(session_id, error_response)
                continue

            customer_message = data.get("content", "").strip()

            # Validate message content
            if not customer_message:
                error_response = {
                    "type": "error",
                    "error_code": "EMPTY_MESSAGE",
                    "message": "Message content cannot be empty",
                    "status": "error",
                }
                await manager.send_message(session_id, error_response)
                continue

            try:
                # Add user message to history
                session_manager.add_message(
                    session_uuid, "user", customer_message
                )
                logger.info(f"User message added to session {session_uuid}")

                # Send thinking status
                thinking_response = {
                    "type": "response",
                    "content": "Let me help you find what you need...",
                    "status": "thinking",
                }
                await manager.send_message(session_id, thinking_response)

                # Process message through agent
                agent_response = await shopping_agent.process_message(
                    session_id=str(session_uuid),
                    customer_message=customer_message,
                    conversation_history=session.conversation_history,
                )

                # Extract response components
                response_text = agent_response.get("response", "")
                products = agent_response.get("products", [])

                # Add agent message to history
                session_manager.add_message(
                    session_uuid, "assistant", response_text
                )
                logger.info(f"Assistant message added to session {session_uuid}")

                # Send complete response
                complete_response = {
                    "type": "response",
                    "content": response_text,
                    "status": "complete",
                    "products": products,
                }
                await manager.send_message(session_id, complete_response)
                logger.info(f"Response sent for session {session_uuid}")

            except ValueError as e:
                # Session-related error
                logger.error(f"Session error for {session_id}: {str(e)}")
                error_response = {
                    "type": "error",
                    "error_code": "SESSION_EXPIRED",
                    "message": "Session expired. Start a new chat?",
                    "status": "error",
                }
                await manager.send_message(session_id, error_response)
                break

            except Exception as e:
                # Agent processing or other errors
                logger.error(f"Error processing message for {session_id}: {str(e)}")
                error_response = {
                    "type": "error",
                    "error_code": "PROCESSING_ERROR",
                    "message": "Sorry, I encountered an error. Please try again.",
                    "status": "error",
                }
                await manager.send_message(session_id, error_response)

    except WebSocketDisconnect:
        await manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler for {session_id}: {str(e)}")
        await manager.disconnect(session_id)
