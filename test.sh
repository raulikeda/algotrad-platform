#!/bin/bash

echo "🧪 Running Home Broker Simulator Tests"
echo "======================================"

# Check if backend is running
echo "📡 Checking if backend is running..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running. Please start it first with:"
    echo "   cd backend && python3 main.py"
    exit 1
fi

# Check if frontend is running
echo "🌐 Checking if frontend is running..."
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend is not running. You can start it with:"
    echo "   cd frontend && npm start"
fi

echo ""
echo "🎯 Basic API Tests:"
echo "=================="

# Test health endpoint
echo "1. Testing health endpoint..."
response=$(curl -s http://localhost:8000/)
if echo "$response" | grep -q "Home Broker Simulator API"; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
fi

# Test user endpoint
echo "2. Testing user endpoint..."
response=$(curl -s http://localhost:8000/api/user)
if echo "$response" | grep -q "user_id"; then
    echo "   ✅ User endpoint passed"
else
    echo "   ❌ User endpoint failed"
fi

# Test order book endpoint
echo "3. Testing order book endpoint..."
response=$(curl -s http://localhost:8000/api/orderbook)
if echo "$response" | grep -q "bids"; then
    echo "   ✅ Order book endpoint passed"
else
    echo "   ❌ Order book endpoint failed"
fi

# Test API documentation
echo "4. Testing API documentation..."
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$response_code" = "200" ]; then
    echo "   ✅ API docs available at http://localhost:8000/docs"
else
    echo "   ❌ API docs not accessible"
fi

echo ""
echo "🌐 URLs to test manually:"
echo "======================="
echo "• Frontend:        http://localhost:3000"
echo "• Backend API:     http://localhost:8000"
echo "• API Docs:        http://localhost:8000/docs"
echo "• Health Check:    http://localhost:8000/"
echo ""

echo "🧪 Manual Testing Checklist:"
echo "==========================="
echo "□ Open frontend at http://localhost:3000"
echo "□ Check that user balance shows $10,000"
echo "□ Place a limit buy order (e.g., 0.001 BTC at $40,000)"
echo "□ Verify order appears in 'Open Orders' section"
echo "□ Check order book shows your bid"
echo "□ Cancel the order"
echo "□ Place a market buy order"
echo "□ Verify balance updates after trade"
echo "□ Check trade appears in history"
echo "□ Test with multiple browser tabs (different users)"
echo ""

echo "✨ If all manual tests pass, your Home Broker Simulator is working perfectly!"
