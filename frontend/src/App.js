import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';
import OrderForm from './components/OrderForm';
import OpenOrders from './components/OpenOrders';
import TradeHistory from './components/TradeHistory';
import UserBalance from './components/UserBalance';
import MarketData from './components/MarketData';

const API_BASE = process.env.REACT_APP_API_URL || 'http://54.81.44.189:8001';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://54.81.44.189:8001/ws';

function App() {
  // State management
  const [userInfo, setUserInfo] = useState(null);
  const [orderBook, setOrderBook] = useState({ bids: [], asks: [], last_price: null });
  const [openOrders, setOpenOrders] = useState([]);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [marketData, setMarketData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState(null);

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    try {
      const websocket = new WebSocket(WS_URL);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('WebSocket message:', message);
        
        switch (message.type) {
          case 'user_info':
            setUserInfo(message.data);
            break;
          case 'order_book':
          case 'order_book_update':
            setOrderBook(message.data);
            break;
          case 'fill':
            // Refresh user info and trade history on fill
            fetchUserInfo();
            fetchTradeHistory();
            fetchOpenOrders();
            break;
          case 'balance_update':
            // Update user balance directly
            setUserInfo(prev => ({
              ...prev,
              cash_balance: message.data.cash_balance,
              asset_balance: message.data.asset_balance
            }));
            break;
          case 'orders_update':
            // Update orders directly
            setOpenOrders(message.data);
            break;
          case 'market_data':
            setMarketData(message.data);
            break;
          default:
            console.log('Unknown message type:', message.type);
        }
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setWs(null);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
      
      return websocket;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setTimeout(connectWebSocket, 3000);
    }
  }, []);

  // API calls
  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/user`, { withCredentials: true });
      setUserInfo(response.data);
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
  };

  const fetchOpenOrders = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/orders`, { withCredentials: true });
      setOpenOrders(response.data.orders);
    } catch (error) {
      console.error('Error fetching open orders:', error);
    }
  };

  const fetchTradeHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/trades`, { withCredentials: true });
      setTradeHistory(response.data.trades);
    } catch (error) {
      console.error('Error fetching trade history:', error);
    }
  };

  const fetchOrderBook = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/orderbook`);
      setOrderBook(response.data);
    } catch (error) {
      console.error('Error fetching order book:', error);
    }
  };

  // Order operations
  const placeOrder = async (orderData) => {
    try {
      const response = await axios.post(`${API_BASE}/api/orders`, orderData, { 
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' }
      });
      
      console.log('Order placed:', response.data);
      
      // Refresh data
      await Promise.all([
        fetchUserInfo(),
        fetchOpenOrders(),
        fetchTradeHistory()
      ]);
      
      return response.data;
    } catch (error) {
      console.error('Error placing order:', error);
      throw error;
    }
  };

  const cancelOrder = async (orderId) => {
    try {
      const response = await axios.delete(`${API_BASE}/api/orders/${orderId}`, { 
        withCredentials: true 
      });
      
      console.log('Order cancelled:', response.data);
      
      // Refresh data
      await fetchOpenOrders();
      
      return response.data;
    } catch (error) {
      console.error('Error cancelling order:', error);
      throw error;
    }
  };

  const updateOrder = async (orderId, updateData) => {
    try {
      const response = await axios.put(`${API_BASE}/api/orders/${orderId}`, updateData, { 
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' }
      });
      
      console.log('Order updated:', response.data);
      
      // Refresh data
      await fetchOpenOrders();
      
      return response.data;
    } catch (error) {
      console.error('Error updating order:', error);
      throw error;
    }
  };

  // Initialize app
  useEffect(() => {
    // Connect WebSocket
    connectWebSocket();
    
    // Fetch initial data
    fetchUserInfo();
    fetchOpenOrders();
    fetchTradeHistory();
    fetchOrderBook();

    // Cleanup WebSocket on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏠 Home Broker Simulator</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
      </header>

      <main className="App-main">
        <div className="trading-layout">
          {/* Left Panel - User Info and Order Form */}
          <div className="left-panel">
            <UserBalance userInfo={userInfo} />
            <OrderForm 
              onPlaceOrder={placeOrder} 
              currentPrice={orderBook.last_price || marketData?.price}
              orderBook={orderBook}
            />
          </div>

          {/* Center Panel - Market Data */}
          <div className="center-panel">
            <MarketData marketData={marketData} />
          </div>

          {/* Right Panel - Orders and Trade History */}
          <div className="right-panel">
            <OpenOrders 
              orders={openOrders} 
              onCancelOrder={cancelOrder}
              onUpdateOrder={updateOrder}
            />
            <TradeHistory trades={tradeHistory} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
