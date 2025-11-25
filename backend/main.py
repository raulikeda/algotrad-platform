"""
Home Broker Simulator - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Cookie, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Any
import uuid
import json
import asyncio
import logging
from datetime import datetime
import websockets

from models import Order, OrderType, OrderSide, Fill, User, OrderBook, BookLevel
from order_matching import OrderMatchingEngine
from websocket_manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Home Broker Simulator", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://54.81.44.189",      # Without port
        "http://54.81.44.189:80",   # HTTP default port
        "http://54.81.44.189:3000", # React dev port
        "https://54.81.44.189",     # HTTPS without port
        "https://54.81.44.189:443", # HTTPS default port
        "http://localhost:3000",    # Local development
        "http://localhost:80",      # Local HTTP
        "*"                         # Allow all origins temporarily for debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug middleware to log all requests
@app.middleware("http")
async def debug_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Global state
users: Dict[str, User] = {}
order_matching_engine = OrderMatchingEngine()
connection_manager = ConnectionManager()


def get_or_create_user(response: Response, user_id: Optional[str] = Cookie(None)) -> tuple[User, str]:
    """Get existing user or create new one based on cookie"""
    if not user_id or user_id not in users:
        user_id = str(uuid.uuid4())
        users[user_id] = User(
            id=user_id,
            cash_balance=10000.0,  # Starting with $10,000
            asset_balance=0.0,     # Starting with 0 shares
        )
        # Set cookie to persist user session
        response.set_cookie(
            key="user_id", 
            value=user_id, 
            max_age=86400*30,  # 30 days
            httponly=False,    # Allow JavaScript access for debugging
            secure=False,      # Set to True in production with HTTPS
            samesite="lax"
        )
        logger.info(f"Created new user: {user_id}")
    
    return users[user_id], user_id


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Start market data feed simulation
    asyncio.create_task(simulate_market_data())
    logger.info("Home Broker Simulator started")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Home Broker Simulator API", "status": "running"}


@app.get("/api/user")
async def get_user_info(response: Response, user_data=Depends(get_or_create_user)):
    """Get current user information"""
    user, user_id = user_data
    return {
        "user_id": user_id,
        "cash_balance": user.cash_balance,
        "asset_balance": user.asset_balance,
        "total_value": user.cash_balance + (user.asset_balance * order_matching_engine.get_last_price())
    }


@app.post("/api/orders")
async def place_order(
    order_data: dict,
    response: Response,
    user_data=Depends(get_or_create_user)
):
    """Place a new order"""
    user, user_id = user_data
    
    try:
        print(order_data)
        # Create order object
        order = Order(
            id=str(uuid.uuid4()),
            user_id=user_id,
            symbol="BTCUSD",  # Single asset for now
            order_type=OrderType(order_data["order_type"]),
            side=OrderSide(order_data["side"]),
            quantity=float(order_data["quantity"]),
            price=float(order_data.get("price", 0)) if order_data.get("price") else None,
            timestamp=datetime.utcnow()
        )
        
        # Validate order against user balance
        if not _validate_order_balance(order, user):
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Process order through matching engine
        fills = order_matching_engine.process_order(order)
        
        # Process fills and update balances
        for fill in fills:
            await _process_fill(fill)
        
        # Broadcast order book update
        await connection_manager.broadcast_order_book(order_matching_engine.get_order_book())
        
        return {"order_id": order.id, "status": "submitted", "fills": len(fills)}
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/orders/{order_id}")
async def cancel_order(
    order_id: str,
    response: Response,
    user_data=Depends(get_or_create_user)
):
    """Cancel an existing order"""
    user, user_id = user_data
    
    try:
        success = order_matching_engine.cancel_order(order_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Order not found or already filled")
        
        # Broadcast order book update
        await connection_manager.broadcast_order_book(order_matching_engine.get_order_book())
        
        return {"status": "cancelled", "order_id": order_id}
        
    except Exception as e:
        logger.error(f"Error canceling order: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/orders/{order_id}")
async def update_order(
    order_id: str,
    update_data: dict,
    response: Response,
    user_data=Depends(get_or_create_user)
):
    """Update an existing order"""
    user, user_id = user_data
    
    try:
        new_price = update_data.get("price")
        new_quantity = update_data.get("quantity")
        
        success = order_matching_engine.update_order(
            order_id, user_id, new_price, new_quantity
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Order not found or cannot be updated")
        
        # Broadcast order book update
        await connection_manager.broadcast_order_book(order_matching_engine.get_order_book())
        
        return {"status": "updated", "order_id": order_id}
        
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/orders")
async def get_open_orders(response: Response, user_data=Depends(get_or_create_user)):
    """Get user's open orders"""
    user, user_id = user_data
    orders = order_matching_engine.get_user_orders(user_id)
    
    return {
        "orders": [
            {
                "id": order.id,
                "symbol": order.symbol,
                "order_type": order.order_type.value,
                "side": order.side.value,
                "quantity": order.quantity,
                "filled_quantity": order.filled_quantity,
                "remaining_quantity": order.remaining_quantity,
                "price": order.price,
                "status": order.status.value,
                "timestamp": order.timestamp.isoformat()
            }
            for order in orders
        ]
    }


@app.get("/api/trades")
async def get_trade_history(response: Response, user_data=Depends(get_or_create_user)):
    """Get user's trade history"""
    user, user_id = user_data
    fills = order_matching_engine.get_user_fills(user_id)
    
    return {
        "trades": [
            {
                "id": fill.id,
                "order_id": fill.order_id,
                "symbol": fill.symbol,
                "side": fill.get_side_for_user(user_id).value,
                "quantity": fill.quantity,
                "price": fill.price,
                "timestamp": fill.timestamp.isoformat()
            }
            for fill in fills
        ]
    }


@app.get("/api/orderbook")
async def get_order_book():
    """Get current order book"""
    return order_matching_engine.get_order_book()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: Optional[str] = Cookie(None)):
    """WebSocket endpoint for real-time updates"""
    if not user_id or user_id not in users:
        user_id = str(uuid.uuid4())
        users[user_id] = User(
            id=user_id,
            cash_balance=10000.0,
            asset_balance=0.0,
        )
    
    await connection_manager.connect(websocket, user_id)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "user_info",
            "data": {
                "user_id": user_id,
                "cash_balance": users[user_id].cash_balance,
                "asset_balance": users[user_id].asset_balance,
            }
        })
        
        await websocket.send_json({
            "type": "order_book",
            "data": order_matching_engine.get_order_book()
        })
        
        # Keep connection alive and handle messages
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)


def _validate_order_balance(order: Order, user: User) -> bool:
    """Validate if user has sufficient balance for the order"""
    if order.side == OrderSide.BUY:
        if order.order_type == OrderType.MARKET:
            # For market orders, check against current ask price
            best_ask = order_matching_engine.get_best_ask()
            if best_ask is None:
                # No asks available, use a high default price for validation
                best_ask = order_matching_engine.get_last_price() * 1.1  # 10% above last price
            required_cash = order.quantity * best_ask
        else:
            # For limit orders, check against limit price
            required_cash = order.quantity * order.price
        return user.cash_balance >= required_cash
    else:
        # For sell orders, allow short selling - no balance check needed
        # Users can sell more than they own (go negative on asset balance)
        return True


async def _process_fill(fill: Fill):
    """Process a fill and update user balances"""
    buyer_id = fill.buyer_id
    seller_id = fill.seller_id
    
    # Update buyer balance (skip if it's a synthetic market fill)
    if buyer_id in users and buyer_id != "MARKET":
        users[buyer_id].cash_balance -= fill.quantity * fill.price
        users[buyer_id].asset_balance += fill.quantity
    
    # Update seller balance (skip if it's a synthetic market fill)  
    if seller_id in users and seller_id != "MARKET":
        users[seller_id].cash_balance += fill.quantity * fill.price
        users[seller_id].asset_balance -= fill.quantity
    
    # Broadcast fill to relevant users (only real users, not synthetic market)
    if buyer_id != "MARKET" and buyer_id in users:
        await connection_manager.send_to_user(buyer_id, {
            "type": "fill",
            "data": {
                "id": fill.id,
                "side": "buy",
                "quantity": fill.quantity,
                "price": fill.price,
                "timestamp": fill.timestamp.isoformat(),
                "new_cash_balance": users[buyer_id].cash_balance,
                "new_asset_balance": users[buyer_id].asset_balance,
            }
        })
    
    if seller_id != "MARKET" and seller_id in users:
        await connection_manager.send_to_user(seller_id, {
            "type": "fill",
            "data": {
                "id": fill.id,
                "side": "sell",
                "quantity": fill.quantity,
                "price": fill.price,
                "timestamp": fill.timestamp.isoformat(),
                "new_cash_balance": users[seller_id].cash_balance,
                "new_asset_balance": users[seller_id].asset_balance,
            }
        })


async def simulate_market_data():
    """Simulate market data feed (like Binance WebSocket)"""
    import random
    
    base_price = 100000.0  # Starting BTC price
    
    while True:
        try:
            # Simulate price movement
            price_change = random.uniform(-100, 100)
            base_price = max(1000, base_price + price_change)
            
            # Round base price to tick size of 10
            base_price = round(base_price / 10) * 10
            
            # Create fake book depth
            bid_levels = []
            ask_levels = []
            
            for i in range(5):  # 5 levels each side
                bid_price = base_price - (i + 1) * random.uniform(10, 50)  # Changed to 10 minimum
                ask_price = base_price + (i + 1) * random.uniform(10, 50)  # Changed to 10 minimum
                bid_size = random.uniform(0.1, 2.0)
                ask_size = random.uniform(0.1, 2.0)
                
                # Round to tick size of 10
                bid_price = round(bid_price / 10) * 10
                ask_price = round(ask_price / 10) * 10
                
                bid_levels.append(BookLevel(price=bid_price, quantity=bid_size))
                ask_levels.append(BookLevel(price=ask_price, quantity=ask_size))
            
            # Update the order book with market data and get any resulting fills
            fills = order_matching_engine.update_market_data(bid_levels, ask_levels)
            
            # Debug logging
            if fills:
                logger.info(f"Market data update resulted in {len(fills)} fills")
                for fill in fills:
                    logger.info(f"Fill: {fill.buyer_id} bought {fill.quantity} at {fill.price}")
                    # Check if the order was actually updated to filled status
                    if fill.buyer_id != "MARKET":
                        buyer_orders = order_matching_engine.get_user_orders(fill.buyer_id)
                        for order in buyer_orders:
                            if order.id == fill.buyer_order_id:
                                logger.info(f"Order {order.id} status after fill: {order.status}")
                    if fill.seller_id != "MARKET":
                        seller_orders = order_matching_engine.get_user_orders(fill.seller_id)
                        for order in seller_orders:
                            if order.id == fill.seller_order_id:
                                logger.info(f"Order {order.id} status after fill: {order.status}")
            
            # Process any fills from limit orders matched against market data
            for fill in fills:
                await _process_fill(fill)
            
            # Broadcast order book update if there were fills
            if fills:
                await connection_manager.broadcast_order_book(order_matching_engine.get_order_book())
                
                # Also broadcast updated user data for each user involved in fills
                for fill in fills:
                    if fill.buyer_id != "MARKET" and fill.buyer_id in users:
                        # Send updated balance to buyer
                        await connection_manager.send_to_user(fill.buyer_id, {
                            "type": "balance_update",
                            "data": {
                                "cash_balance": users[fill.buyer_id].cash_balance,
                                "asset_balance": users[fill.buyer_id].asset_balance
                            }
                        })
                        # Send updated orders to buyer
                        user_orders = order_matching_engine.get_user_orders(fill.buyer_id)
                        await connection_manager.send_to_user(fill.buyer_id, {
                            "type": "orders_update", 
                            "data": [order.to_dict() for order in user_orders]
                        })
                        
                    if fill.seller_id != "MARKET" and fill.seller_id in users:
                        # Send updated balance to seller
                        await connection_manager.send_to_user(fill.seller_id, {
                            "type": "balance_update",
                            "data": {
                                "cash_balance": users[fill.seller_id].cash_balance,
                                "asset_balance": users[fill.seller_id].asset_balance
                            }
                        })
                        # Send updated orders to seller
                        user_orders = order_matching_engine.get_user_orders(fill.seller_id)
                        await connection_manager.send_to_user(fill.seller_id, {
                            "type": "orders_update",
                            "data": [order.to_dict() for order in user_orders]
                        })
            
            # Broadcast to all connected clients
            await connection_manager.broadcast({
                "type": "market_data",
                "data": {
                    "symbol": "BTCUSD",
                    "price": base_price,
                    "bids": [(level.price, level.quantity) for level in bid_levels],
                    "asks": [(level.price, level.quantity) for level in ask_levels],
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            logger.error(f"Error in market data simulation: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
