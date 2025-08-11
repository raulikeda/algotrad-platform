"""
Order Matching Engine for Home Broker Simulator
"""

from typing import Dict, List, Optional
from collections import defaultdict
import heapq
from datetime import datetime
import uuid
import logging

from models import Order, OrderType, OrderSide, OrderStatus, Fill, BookLevel, OrderBook

logger = logging.getLogger(__name__)


class OrderMatchingEngine:
    """
    Simple order matching engine with price-time priority
    """
    
    def __init__(self):
        # Order storage
        self.orders: Dict[str, Order] = {}
        self.user_orders: Dict[str, List[str]] = defaultdict(list)
        
        # Order book - using heaps for efficient price-time priority
        self.buy_orders = []   # Max heap (negative prices for max behavior)
        self.sell_orders = []  # Min heap
        
        # Market data
        self.market_bids: List[BookLevel] = []
        self.market_asks: List[BookLevel] = []
        self.last_price: Optional[float] = None
        
        # Trade history
        self.fills: List[Fill] = []
        self.user_fills: Dict[str, List[Fill]] = defaultdict(list)
    
    def process_order(self, order: Order) -> List[Fill]:
        """
        Process an incoming order and return any fills
        """
        fills = []
        
        # Store the order
        self.orders[order.id] = order
        self.user_orders[order.user_id].append(order.id)
        
        if order.order_type == OrderType.MARKET:
            fills = self._process_market_order(order)
        else:
            fills = self._process_limit_order(order)
        
        # Store fills
        for fill in fills:
            self.fills.append(fill)
            self.user_fills[fill.buyer_id].append(fill)
            self.user_fills[fill.seller_id].append(fill)
            self.last_price = fill.price
        
        logger.info(f"Processed order {order.id}, generated {len(fills)} fills")
        return fills
    
    def _process_market_order(self, order: Order) -> List[Fill]:
        """Process a market order"""
        fills = []
        remaining_qty = order.quantity
        
        if order.side == OrderSide.BUY:
            # Match against sell orders (asks)
            while remaining_qty > 0 and self.sell_orders:
                best_sell = heapq.heappop(self.sell_orders)
                sell_price, sell_timestamp, sell_order_id = best_sell
                
                if sell_order_id not in self.orders:
                    continue
                    
                sell_order = self.orders[sell_order_id]
                if sell_order.status != OrderStatus.PENDING:
                    continue
                
                # Calculate fill quantity
                fill_qty = min(remaining_qty, sell_order.remaining_quantity)
                
                # Create fill
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id=order.id,
                    seller_order_id=sell_order.id,
                    buyer_id=order.user_id,
                    seller_id=sell_order.user_id,
                    symbol=order.symbol,
                    quantity=fill_qty,
                    price=sell_price,
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update orders
                order.filled_quantity += fill_qty
                sell_order.filled_quantity += fill_qty
                remaining_qty -= fill_qty
                
                # Update order status
                if sell_order.is_fully_filled:
                    sell_order.status = OrderStatus.FILLED
                else:
                    sell_order.status = OrderStatus.PARTIAL
                    # Put back partial order
                    heapq.heappush(self.sell_orders, best_sell)
            
            # If still has remaining quantity and no user orders, match against market data
            if remaining_qty > 0 and self.market_asks:
                # Use the best market ask price for execution
                market_price = self.market_asks[0].price
                
                # Create a synthetic fill against market liquidity
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id=order.id,
                    seller_order_id="MARKET_LIQUIDITY",  # Synthetic seller
                    buyer_id=order.user_id,
                    seller_id="MARKET",  # Market maker
                    symbol=order.symbol,
                    quantity=remaining_qty,
                    price=market_price,
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update order
                order.filled_quantity += remaining_qty
                remaining_qty = 0
        
        else:  # SELL
            # Match against buy orders (bids)
            while remaining_qty > 0 and self.buy_orders:
                best_buy = heapq.heappop(self.buy_orders)
                neg_buy_price, buy_timestamp, buy_order_id = best_buy
                buy_price = -neg_buy_price
                
                if buy_order_id not in self.orders:
                    continue
                    
                buy_order = self.orders[buy_order_id]
                if buy_order.status != OrderStatus.PENDING:
                    continue
                
                # Calculate fill quantity
                fill_qty = min(remaining_qty, buy_order.remaining_quantity)
                
                # Create fill
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id=buy_order.id,
                    seller_order_id=order.id,
                    buyer_id=buy_order.user_id,
                    seller_id=order.user_id,
                    symbol=order.symbol,
                    quantity=fill_qty,
                    price=buy_price,
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update orders
                order.filled_quantity += fill_qty
                buy_order.filled_quantity += fill_qty
                remaining_qty -= fill_qty
                
                # Update order status
                if buy_order.is_fully_filled:
                    buy_order.status = OrderStatus.FILLED
                else:
                    buy_order.status = OrderStatus.PARTIAL
                    # Put back partial order
                    heapq.heappush(self.buy_orders, best_buy)
            
            # If still has remaining quantity and no user orders, match against market data
            if remaining_qty > 0 and self.market_bids:
                # Use the best market bid price for execution
                market_price = self.market_bids[0].price
                
                # Create a synthetic fill against market liquidity
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id="MARKET_LIQUIDITY",  # Synthetic buyer
                    seller_order_id=order.id,
                    buyer_id="MARKET",  # Market maker
                    seller_id=order.user_id,
                    symbol=order.symbol,
                    quantity=remaining_qty,
                    price=market_price,
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update order
                order.filled_quantity += remaining_qty
                remaining_qty = 0
        
        # Update market order status
        if order.is_fully_filled:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIAL
        
        return fills
    
    def _process_limit_order(self, order: Order) -> List[Fill]:
        """Process a limit order"""
        fills = []
        remaining_qty = order.quantity
        
        if order.side == OrderSide.BUY:
            # Try to match against existing sell orders
            temp_sells = []
            while remaining_qty > 0 and self.sell_orders:
                best_sell = heapq.heappop(self.sell_orders)
                sell_price, sell_timestamp, sell_order_id = best_sell
                
                # Check if we can match (buy price >= sell price)
                if order.price < sell_price:
                    heapq.heappush(self.sell_orders, best_sell)
                    break
                
                if sell_order_id not in self.orders:
                    continue
                    
                sell_order = self.orders[sell_order_id]
                if sell_order.status != OrderStatus.PENDING:
                    continue
                
                # Calculate fill quantity
                fill_qty = min(remaining_qty, sell_order.remaining_quantity)
                
                # Create fill
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id=order.id,
                    seller_order_id=sell_order.id,
                    buyer_id=order.user_id,
                    seller_id=sell_order.user_id,
                    symbol=order.symbol,
                    quantity=fill_qty,
                    price=sell_price,  # Fill at the resting order's price
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update orders
                order.filled_quantity += fill_qty
                sell_order.filled_quantity += fill_qty
                remaining_qty -= fill_qty
                
                # Update order status
                if sell_order.is_fully_filled:
                    sell_order.status = OrderStatus.FILLED
                else:
                    sell_order.status = OrderStatus.PARTIAL
                    heapq.heappush(self.sell_orders, best_sell)
            
            # If not fully filled, try to match against market data
            if remaining_qty > 0 and self.market_asks:
                # Check if we can match against market ask
                market_ask_price = self.market_asks[0].price
                if order.price >= market_ask_price:
                    # Create a synthetic fill against market liquidity
                    fill = Fill(
                        id=str(uuid.uuid4()),
                        buyer_order_id=order.id,
                        seller_order_id="MARKET_LIQUIDITY",
                        buyer_id=order.user_id,
                        seller_id="MARKET",
                        symbol=order.symbol,
                        quantity=remaining_qty,
                        price=market_ask_price,
                        timestamp=datetime.utcnow()
                    )
                    fills.append(fill)
                    
                    # Update order
                    order.filled_quantity += remaining_qty
                    remaining_qty = 0
            
            # If still not fully filled, add to order book
            if remaining_qty > 0:
                heapq.heappush(self.buy_orders, (
                    -order.price,  # Negative for max heap behavior
                    order.timestamp.timestamp(),
                    order.id
                ))
        
        else:  # SELL
            # Try to match against existing buy orders
            while remaining_qty > 0 and self.buy_orders:
                best_buy = heapq.heappop(self.buy_orders)
                neg_buy_price, buy_timestamp, buy_order_id = best_buy
                buy_price = -neg_buy_price
                
                # Check if we can match (sell price <= buy price)
                if order.price > buy_price:
                    heapq.heappush(self.buy_orders, best_buy)
                    break
                
                if buy_order_id not in self.orders:
                    continue
                    
                buy_order = self.orders[buy_order_id]
                if buy_order.status != OrderStatus.PENDING:
                    continue
                
                # Calculate fill quantity
                fill_qty = min(remaining_qty, buy_order.remaining_quantity)
                
                # Create fill
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id=buy_order.id,
                    seller_order_id=order.id,
                    buyer_id=buy_order.user_id,
                    seller_id=order.user_id,
                    symbol=order.symbol,
                    quantity=fill_qty,
                    price=buy_price,  # Fill at the resting order's price
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update orders
                order.filled_quantity += fill_qty
                buy_order.filled_quantity += fill_qty
                remaining_qty -= fill_qty
                
                # Update order status
                if buy_order.is_fully_filled:
                    buy_order.status = OrderStatus.FILLED
                else:
                    buy_order.status = OrderStatus.PARTIAL
                    heapq.heappush(self.buy_orders, best_buy)
            
            # If not fully filled, try to match against market data
            if remaining_qty > 0 and self.market_bids:
                # Check if we can match against market bid
                market_bid_price = self.market_bids[0].price
                if order.price <= market_bid_price:
                    # Create a synthetic fill against market liquidity
                    fill = Fill(
                        id=str(uuid.uuid4()),
                        buyer_order_id="MARKET_LIQUIDITY",
                        seller_order_id=order.id,
                        buyer_id="MARKET",
                        seller_id=order.user_id,
                        symbol=order.symbol,
                        quantity=remaining_qty,
                        price=market_bid_price,
                        timestamp=datetime.utcnow()
                    )
                    fills.append(fill)
                    
                    # Update order
                    order.filled_quantity += remaining_qty
                    remaining_qty = 0
            
            # If still not fully filled, add to order book
            if remaining_qty > 0:
                heapq.heappush(self.sell_orders, (
                    order.price,
                    order.timestamp.timestamp(),
                    order.id
                ))
        
        # Update limit order status
        if order.is_fully_filled:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIAL
        
        return fills
    
    def cancel_order(self, order_id: str, user_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.user_id != user_id or order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False
        
        order.status = OrderStatus.CANCELLED
        logger.info(f"Cancelled order {order_id}")
        return True
    
    def update_order(self, order_id: str, user_id: str, new_price: Optional[float], new_quantity: Optional[float]) -> bool:
        """Update an order (cancel and replace)"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.user_id != user_id or order.status != OrderStatus.PENDING:
            return False
        
        # Remove the old order from the heap
        self._remove_order_from_heap(order_id, order.side)
        
        # Update the order details
        if new_price is not None:
            order.price = new_price
        if new_quantity is not None:
            order.quantity = new_quantity
            # Reset filled quantity if quantity is updated
            order.filled_quantity = 0
        
        # Add the updated order back to the heap
        if order.side == OrderSide.BUY:
            heapq.heappush(self.buy_orders, (
                -order.price,  # Negative for max heap behavior
                order.timestamp.timestamp(),
                order.id
            ))
        else:
            heapq.heappush(self.sell_orders, (
                order.price,
                order.timestamp.timestamp(),
                order.id
            ))
        
        logger.info(f"Updated order {order_id}")
        return True
    
    def _remove_order_from_heap(self, order_id: str, side: OrderSide):
        """Remove an order from the appropriate heap"""
        if side == OrderSide.BUY:
            # Mark for removal by filtering out the order
            self.buy_orders = [entry for entry in self.buy_orders if entry[2] != order_id]
            heapq.heapify(self.buy_orders)
        else:
            # Mark for removal by filtering out the order
            self.sell_orders = [entry for entry in self.sell_orders if entry[2] != order_id]
            heapq.heapify(self.sell_orders)
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """Get all orders for a user"""
        order_ids = self.user_orders.get(user_id, [])
        return [self.orders[order_id] for order_id in order_ids if order_id in self.orders]
    
    def get_user_fills(self, user_id: str) -> List[Fill]:
        """Get all fills for a user"""
        return self.user_fills.get(user_id, [])
    
    def get_order_book(self) -> dict:
        """Get current order book state"""
        # Aggregate orders by price level
        bid_levels = defaultdict(float)
        ask_levels = defaultdict(float)
        
        # Process buy orders
        for neg_price, timestamp, order_id in self.buy_orders:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.status == OrderStatus.PENDING:
                    price = -neg_price
                    bid_levels[price] += order.remaining_quantity
        
        # Process sell orders
        for price, timestamp, order_id in self.sell_orders:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.status == OrderStatus.PENDING:
                    ask_levels[price] += order.remaining_quantity
        
        # Convert to sorted lists
        bids = sorted([(price, qty) for price, qty in bid_levels.items()], reverse=True)[:10]
        asks = sorted([(price, qty) for price, qty in ask_levels.items()])[:10]
        
        return {
            "symbol": "BTCUSD",
            "bids": bids,
            "asks": asks,
            "last_price": self.last_price,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_best_bid(self) -> Optional[float]:
        """Get best bid price"""
        if not self.buy_orders:
            return None
        return -self.buy_orders[0][0]
    
    def get_best_ask(self) -> Optional[float]:
        """Get best ask price"""
        if not self.sell_orders:
            return None
        return self.sell_orders[0][0]
    
    def get_last_price(self) -> float:
        """Get last traded price"""
        return self.last_price or 45000.0  # Default price
    
    def update_market_data(self, bids: List[BookLevel], asks: List[BookLevel]):
        """Update market data from external feed and check for limit order fills"""
        self.market_bids = bids
        self.market_asks = asks
        
        # Debug logging
        pending_buy_orders = sum(1 for order in self.orders.values() 
                               if order.side == 'buy' and order.status == OrderStatus.PENDING)
        pending_sell_orders = sum(1 for order in self.orders.values() 
                                if order.side == 'sell' and order.status == OrderStatus.PENDING)
        
        if pending_buy_orders > 0 or pending_sell_orders > 0:
            print(f"Checking market data: {pending_buy_orders} pending buy orders, {pending_sell_orders} pending sell orders")
            print(f"Market ask: {asks[0].price if asks else 'None'}, Market bid: {bids[0].price if bids else 'None'}")
        
        # Check existing limit orders against new market prices
        return self._check_limit_orders_against_market()
    
    def _check_limit_orders_against_market(self):
        """Check existing limit orders against current market data for potential fills"""
        fills = []
        
        # Debug logging
        pending_orders = [order for order in self.orders.values() if order.status == OrderStatus.PENDING]
        if pending_orders:
            print(f"DEBUG: Checking {len(pending_orders)} pending orders against market data")
            for order in pending_orders:
                print(f"DEBUG: Pending order {order.id}: {order.side} {order.remaining_quantity} at {order.price}")
        
        # Check buy orders against market asks
        if self.market_asks and len(self.market_asks) > 0:
            market_ask_price = self.market_asks[0].price
            print(f"DEBUG: Market ask price: {market_ask_price}")
            
            # Create a temporary list to hold all buy orders
            temp_buy_orders = []
            buy_orders_to_fill = []
            
            # Extract all buy orders from heap
            while self.buy_orders:
                order_entry = heapq.heappop(self.buy_orders)
                temp_buy_orders.append(order_entry)
            
            print(f"DEBUG: Processing {len(temp_buy_orders)} buy orders from heap")
            
            # Process each order
            for order_entry in temp_buy_orders:
                neg_price, timestamp, order_id = order_entry
                buy_price = -neg_price
                
                if order_id in self.orders:
                    order = self.orders[order_id]
                    
                    # Skip if order is not pending anymore
                    if order.status != OrderStatus.PENDING:
                        continue
                        
                    # Use the actual order price from the order object, not from heap entry
                    # (in case the order was updated but heap wasn't updated properly)
                    actual_price = order.price
                    
                    print(f"DEBUG: Buy order {order_id}: heap_price {buy_price}, actual_price {actual_price}, market ask {market_ask_price}, status {order.status}")
                    
                    # If buy price >= market ask price and order is still pending, it can be filled
                    if actual_price >= market_ask_price:
                        print(f"DEBUG: Buy order {order_id} should fill! {actual_price} >= {market_ask_price}")
                        buy_orders_to_fill.append((order, market_ask_price))
                    else:
                        # Keep pending orders that don't match - put them back in heap with correct price
                        heapq.heappush(self.buy_orders, (
                            -actual_price,
                            timestamp, 
                            order_id
                        ))
                else:
                    print(f"DEBUG: Order {order_id} not found in orders dictionary")
            
            # Fill the matching buy orders
            for order, fill_price in buy_orders_to_fill:
                print(f"DEBUG: Filling buy order {order.id} at {fill_price}")
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id=order.id,
                    seller_order_id="MARKET_LIQUIDITY",
                    buyer_id=order.user_id,
                    seller_id="MARKET",
                    symbol=order.symbol,
                    quantity=order.remaining_quantity,
                    price=fill_price,
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update order status
                order.filled_quantity += order.remaining_quantity
                order.status = OrderStatus.FILLED
                
                # Store the fill in engine's internal state
                self.fills.append(fill)
                if fill.buyer_id != "MARKET":
                    self.user_fills[fill.buyer_id].append(fill)
                if fill.seller_id != "MARKET":
                    self.user_fills[fill.seller_id].append(fill)
                
                # Update last price
                self.last_price = fill.price
        
        # Check sell orders against market bids
        if self.market_bids and len(self.market_bids) > 0:
            market_bid_price = self.market_bids[0].price
            print(f"DEBUG: Market bid price: {market_bid_price}")
            
            # Create a temporary list to hold all sell orders
            temp_sell_orders = []
            sell_orders_to_fill = []
            
            # Extract all sell orders from heap
            while self.sell_orders:
                order_entry = heapq.heappop(self.sell_orders)
                temp_sell_orders.append(order_entry)
            
            print(f"DEBUG: Processing {len(temp_sell_orders)} sell orders from heap")
            
            # Process each order
            for order_entry in temp_sell_orders:
                price, timestamp, order_id = order_entry
                
                if order_id in self.orders:
                    order = self.orders[order_id]
                    
                    # Skip if order is not pending anymore
                    if order.status != OrderStatus.PENDING:
                        continue
                        
                    # Use the actual order price from the order object, not from heap entry
                    # (in case the order was updated but heap wasn't updated properly)
                    actual_price = order.price
                    
                    print(f"DEBUG: Sell order {order_id}: heap_price {price}, actual_price {actual_price}, market bid {market_bid_price}, status {order.status}")
                    
                    # If sell price <= market bid price and order is still pending, it can be filled
                    if actual_price <= market_bid_price:
                        print(f"DEBUG: Sell order {order_id} should fill! {actual_price} <= {market_bid_price}")
                        sell_orders_to_fill.append((order, market_bid_price))
                    else:
                        # Keep pending orders that don't match - put them back in heap with correct price
                        heapq.heappush(self.sell_orders, (
                            actual_price,
                            timestamp,
                            order_id
                        ))
                else:
                    print(f"DEBUG: Order {order_id} not found in orders dictionary")
            
            # Fill the matching sell orders
            for order, fill_price in sell_orders_to_fill:
                print(f"DEBUG: Filling sell order {order.id} at {fill_price}")
                fill = Fill(
                    id=str(uuid.uuid4()),
                    buyer_order_id="MARKET_LIQUIDITY",
                    seller_order_id=order.id,
                    buyer_id="MARKET",
                    seller_id=order.user_id,
                    symbol=order.symbol,
                    quantity=order.remaining_quantity,
                    price=fill_price,
                    timestamp=datetime.utcnow()
                )
                fills.append(fill)
                
                # Update order status
                order.filled_quantity += order.remaining_quantity
                order.status = OrderStatus.FILLED
                
                # Store the fill in engine's internal state
                self.fills.append(fill)
                if fill.buyer_id != "MARKET":
                    self.user_fills[fill.buyer_id].append(fill)
                if fill.seller_id != "MARKET":
                    self.user_fills[fill.seller_id].append(fill)
                
                # Update last price
                self.last_price = fill.price
        
        return fills
    
    def _process_fill(self, fill: Fill):
        """Process a fill and update internal state"""
        # Add fill to user's fill history
        if fill.buyer_id != "MARKET":
            if fill.buyer_id not in self.user_fills:
                self.user_fills[fill.buyer_id] = []
            self.user_fills[fill.buyer_id].append(fill)
        
        if fill.seller_id != "MARKET":
            if fill.seller_id not in self.user_fills:
                self.user_fills[fill.seller_id] = []
            self.user_fills[fill.seller_id].append(fill)
        
        # Update last price
        self.last_price = fill.price
        
        logger.info(f"Processed fill: {fill.quantity} at {fill.price} between {fill.buyer_id} and {fill.seller_id}")
