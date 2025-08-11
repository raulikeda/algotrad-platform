import React, { useState } from 'react';

const OrderForm = ({ onPlaceOrder, currentPrice, orderBook }) => {
  const [orderData, setOrderData] = useState({
    order_type: 'market',
    quantity: '0.01',
    price: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // If changing to limit order, auto-fill price with current price
    if (name === 'order_type' && value === 'limit') {
      let priceToFill = '';
      
      // First try to use mid price from order book
      if (orderBook) {
        const midPrice = calculateMidPrice();
        if (midPrice) {
          priceToFill = midPrice.toString();
        }
      }
      
      // Fallback to current price if no order book or mid price
      if (!priceToFill && currentPrice) {
        // Round current price to tick size of 10
        const roundedPrice = Math.round(currentPrice / 10) * 10;
        priceToFill = roundedPrice.toString();
      }
      
      setOrderData(prev => ({
        ...prev,
        [name]: value,
        price: priceToFill
      }));
    } else {
      setOrderData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    setError(''); // Clear error when user types
  };

  const calculateMidPrice = () => {
    if (!orderBook || !orderBook.bids || !orderBook.asks) return null;
    if (orderBook.bids.length === 0 || orderBook.asks.length === 0) return null;
    
    const bestBid = orderBook.bids[0][0]; // First element is price
    const bestAsk = orderBook.asks[0][0]; // First element is price
    
    const midPrice = (bestBid + bestAsk) / 2;
    // Round to tick size of 10
    return Math.round(midPrice / 10) * 10;
  };

  const handleOrderSubmit = async (side) => {
    setIsSubmitting(true);
    setError('');

    try {
      // Validate form
      if (!orderData.quantity || parseFloat(orderData.quantity) <= 0) {
        throw new Error('Please enter a valid quantity');
      }

      if (orderData.order_type === 'limit' && (!orderData.price || parseFloat(orderData.price) <= 0)) {
        throw new Error('Please enter a valid price for limit orders');
      }

      // Prepare order data
      const order = {
        order_type: orderData.order_type,
        side: side,
        quantity: parseFloat(orderData.quantity),
      };

      if (orderData.order_type === 'limit') {
        order.price = parseFloat(orderData.price);
      }

      await onPlaceOrder(order);

      // Reset form on success
      setOrderData({
        order_type: 'market',
        quantity: '0.01',
        price: ''
      });

    } catch (err) {
      console.error('Order submission error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to place order');
    } finally {
      setIsSubmitting(false);
    }
  };

  const estimatedTotal = () => {
    if (!orderData.quantity) return 0;
    
    const quantity = parseFloat(orderData.quantity);
    let price;
    
    if (orderData.order_type === 'market') {
      price = currentPrice || 45000;
    } else {
      price = parseFloat(orderData.price) || 0;
    }
    
    return quantity * price;
  };

  return (
    <div className="trading-card">
      <h2>📋 Place Order</h2>
      
      {error && (
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.1)', 
          border: '1px solid #ef4444', 
          borderRadius: '8px', 
          padding: '0.75rem', 
          marginBottom: '1rem',
          color: '#dc2626'
        }}>
          {error}
        </div>
      )}

      <form>
        <div className="form-group">
          <label htmlFor="order_type">Order Type</label>
          <select
            id="order_type"
            name="order_type"
            value={orderData.order_type}
            onChange={handleInputChange}
            className="form-control"
            style={{ color: '#000' }}
          >
            <option value="market">Market Order</option>
            <option value="limit">Limit Order</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity (BTC)</label>
          <input
            type="number"
            id="quantity"
            name="quantity"
            value={orderData.quantity}
            onChange={handleInputChange}
            placeholder="0.01"
            step="0.01"
            min="0"
            className="form-control"
            style={{ color: '#000' }}
          />
        </div>

        {orderData.order_type === 'limit' && (
          <div className="form-group">
            <label htmlFor="price">Price (USD)</label>
            <input
              type="number"
              id="price"
              name="price"
              value={orderData.price}
              onChange={handleInputChange}
              placeholder="100000.00"
              step="10"
              min="0"
              className="form-control"
              style={{ color: '#000' }}
            />
          </div>
        )}

        {currentPrice && (
          <div style={{ 
            background: '#f8fafc', 
            border: '1px solid #e2e8f0',
            padding: '0.75rem', 
            borderRadius: '8px', 
            marginBottom: '1rem',
            fontSize: '0.9rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>Current Price:</span>
              <span style={{ color: '#1f2937', fontWeight: '600' }}>${currentPrice.toLocaleString()}</span>
            </div>
            {orderData.quantity && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Estimated Total:</span>
                <span style={{ color: '#1f2937', fontWeight: '600' }}>${estimatedTotal().toLocaleString()}</span>
              </div>
            )}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-success"
            disabled={isSubmitting}
            style={{ flex: 1 }}
            onClick={() => handleOrderSubmit('buy')}
          >
            {isSubmitting ? 'Placing...' : `BUY ${orderData.quantity || '0'} BTC`}
          </button>
          
          <button
            type="button"
            className="btn btn-danger"
            disabled={isSubmitting}
            style={{ flex: 1 }}
            onClick={() => handleOrderSubmit('sell')}
          >
            {isSubmitting ? 'Placing...' : `SELL ${orderData.quantity || '0'} BTC`}
          </button>
        </div>
      </form>
    </div>
  );
};

export default OrderForm;
