# 🏠 Home Broker Trading Simulator

A comprehensive trading simulation platform that mimics a real home broker interface. This project allows users to practice trading with realistic order matching, real-time market data, and portfolio management without real money at risk.

## 🧠 Purpose

The Home Broker Simulator provides:
- **Realistic Trading Experience**: Simulate market and limit orders with real-time order book
- **User Separation**: Multiple users can trade simultaneously (cookie-based identification)  
- **Order Matching Engine**: Full price-time priority matching with partial fills
- **Real-time Updates**: WebSocket-powered live updates for order book and fills
- **Portfolio Tracking**: Monitor cash and asset balances with trade history

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ Order Matching  │
│                 │◄──►│                 │◄──►│    Engine       │
│ - Trading UI    │    │ - REST API      │    │ - Price-Time    │
│ - WebSocket     │    │ - WebSocket     │    │   Priority      │
│ - Real-time     │    │ - User Mgmt     │    │ - Partial Fills │
│   Updates       │    │ - Balance Mgmt  │    │ - Order Book    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
        └────────── WebSocket ────┴────── Market Data ────┘
```

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend Setup  
```bash
cd frontend
npm install
npm start
```

Visit `http://localhost:3000` to start trading!

## 🔧 Technology Stack

- **Backend**: FastAPI, Python 3.8+, WebSockets
- **Frontend**: React 18, WebSocket Client, Axios
- **Order Matching**: Price-time priority with partial fills
- **Storage**: In-memory (resets on restart)

## 📊 Features

✅ Market & Limit Orders  
✅ Real-time Order Book  
✅ Order Matching Engine  
✅ Multi-user Support  
✅ WebSocket Updates  
✅ Balance Management  
✅ Trade History  
✅ Order Management (Cancel/Update)
