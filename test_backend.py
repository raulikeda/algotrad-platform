"""
Simple test script to verify the Home Broker Simulator backend
"""

import asyncio
import json
import websockets
import aiohttp
import time

async def test_api_endpoints():
    """Test REST API endpoints"""
    print("🧪 Testing API endpoints...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        try:
            async with session.get('http://localhost:8000/') as response:
                data = await response.json()
                print(f"✅ Health check: {data['message']}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        # Test user endpoint
        try:
            async with session.get('http://localhost:8000/api/user') as response:
                data = await response.json()
                print(f"✅ User info: Cash={data['cash_balance']}, BTC={data['asset_balance']}")
                user_id = data['user_id']
        except Exception as e:
            print(f"❌ User endpoint failed: {e}")
            return False
        
        # Test order book endpoint
        try:
            async with session.get('http://localhost:8000/api/orderbook') as response:
                data = await response.json()
                print(f"✅ Order book: {len(data.get('bids', []))} bids, {len(data.get('asks', []))} asks")
        except Exception as e:
            print(f"❌ Order book endpoint failed: {e}")
            return False
        
        # Test placing an order
        try:
            order_data = {
                "order_type": "limit",
                "side": "buy", 
                "quantity": 0.001,
                "price": 40000.0
            }
            async with session.post('http://localhost:8000/api/orders', 
                                  json=order_data) as response:
                data = await response.json()
                print(f"✅ Order placed: {data['order_id']}")
                order_id = data['order_id']
        except Exception as e:
            print(f"❌ Order placement failed: {e}")
            return False
        
        # Test getting open orders
        try:
            async with session.get('http://localhost:8000/api/orders') as response:
                data = await response.json()
                print(f"✅ Open orders: {len(data['orders'])} orders")
        except Exception as e:
            print(f"❌ Open orders endpoint failed: {e}")
            return False
        
        # Test cancelling the order
        try:
            async with session.delete(f'http://localhost:8000/api/orders/{order_id}') as response:
                data = await response.json()
                print(f"✅ Order cancelled: {data['status']}")
        except Exception as e:
            print(f"❌ Order cancellation failed: {e}")
            return False
    
    return True

async def test_websocket():
    """Test WebSocket connection"""
    print("🔌 Testing WebSocket connection...")
    
    try:
        async with websockets.connect('ws://localhost:8000/ws') as websocket:
            print("✅ WebSocket connected")
            
            # Wait for initial messages
            for _ in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(message)
                    print(f"✅ Received: {data['type']}")
                except asyncio.TimeoutError:
                    break
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🏠 Home Broker Simulator - Backend Tests")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    await asyncio.sleep(2)
    
    # Run API tests
    api_success = await test_api_endpoints()
    
    # Run WebSocket tests  
    ws_success = await test_websocket()
    
    print("\n" + "=" * 50)
    if api_success and ws_success:
        print("🎉 All tests passed! Backend is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the backend logs.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        exit(1)
