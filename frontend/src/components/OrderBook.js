import React from 'react';

const OrderBook = ({ orderBook }) => {
  if (!orderBook) {
    return (
      <div className="trading-card">
        <h2>📊 Order Book</h2>
        <div>Loading order book...</div>
      </div>
    );
  }

  const { bids = [], asks = [], last_price } = orderBook;

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatQuantity = (quantity) => {
    return quantity.toFixed(8);
  };

  // Calculate cumulative quantities
  const calculateCumulative = (levels) => {
    let cumulative = 0;
    return levels.map(([price, quantity]) => {
      cumulative += quantity;
      return [price, quantity, cumulative];
    });
  };

  const bidsWithCumulative = calculateCumulative(bids);
  const asksWithCumulative = calculateCumulative(asks);

  return (
    <div className="trading-card">
      <h2>📊 Order Book - BTCUSD</h2>
      
      {last_price && (
        <div style={{ 
          background: '#f8fafc', 
          border: '1px solid #e2e8f0',
          padding: '1rem', 
          borderRadius: '8px', 
          marginBottom: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '0.9rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            Last Price
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', fontFamily: 'Courier New, monospace' }}>
            {formatPrice(last_price)}
          </div>
        </div>
      )}

      <div className="order-book-container">
        {/* Asks (Sell Orders) */}
        <div className="order-book-side asks">
          <h4>🔴 Asks (Sellers)</h4>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280', borderBottom: '1px solid #e5e7eb' }}>
            <span>Price</span>
            <span>Size</span>
            <span>Total</span>
          </div>
          {asksWithCumulative.slice().reverse().map(([price, quantity, cumulative], index) => (
            <div key={`ask-${price}-${index}`} className="order-book-row ask">
              <span className="order-book-price ask">{formatPrice(price)}</span>
              <span className="order-book-quantity">{formatQuantity(quantity)}</span>
              <span className="order-book-quantity">{formatQuantity(cumulative)}</span>
            </div>
          ))}
        </div>

        {/* Spread */}
        {bids.length > 0 && asks.length > 0 && (
          <div style={{ 
            padding: '0.75rem', 
            textAlign: 'center', 
            background: '#f8fafc', 
            border: '1px solid #e2e8f0',
            margin: '1rem 0',
            borderRadius: '4px'
          }}>
            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Spread</div>
            <div style={{ fontSize: '1rem', fontWeight: '600', color: '#1f2937' }}>
              {formatPrice(asks[0][0] - bids[0][0])}
            </div>
          </div>
        )}

        {/* Bids (Buy Orders) */}
        <div className="order-book-side bids">
          <h4>🟢 Bids (Buyers)</h4>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280', borderBottom: '1px solid #e5e7eb' }}>
            <span>Price</span>
            <span>Size</span>
            <span>Total</span>
          </div>
          {bidsWithCumulative.map(([price, quantity, cumulative], index) => (
            <div key={`bid-${price}-${index}`} className="order-book-row bid">
              <span className="order-book-price bid">{formatPrice(price)}</span>
              <span className="order-book-quantity">{formatQuantity(quantity)}</span>
              <span className="order-book-quantity">{formatQuantity(cumulative)}</span>
            </div>
          ))}
        </div>

        {(bids.length === 0 && asks.length === 0) && (
          <div style={{ 
            textAlign: 'center', 
            padding: '2rem', 
            color: '#6b7280',
            fontStyle: 'italic'
          }}>
            No orders in the book
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderBook;
