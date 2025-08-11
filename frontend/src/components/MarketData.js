import React from 'react';

const MarketData = ({ marketData }) => {
  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatQuantity = (quantity) => {
    return quantity.toFixed(4);
  };

  if (!marketData) {
    return (
      <div className="trading-card">
        <h2>📊 Market Data</h2>
        <div style={{ 
          textAlign: 'center', 
          padding: '2rem', 
          color: '#94a3b8',
          fontStyle: 'italic'
        }}>
          Waiting for market data...
        </div>
      </div>
    );
  }

  const { symbol, price, bids = [], asks = [], timestamp } = marketData;

  const bestBid = bids.length > 0 ? bids[0] : null;
  const bestAsk = asks.length > 0 ? asks[0] : null;
  const spread = bestBid && bestAsk ? bestAsk[0] - bestBid[0] : 0;
  const spreadPercent = bestBid && bestAsk ? ((spread / bestBid[0]) * 100) : 0;

  return (
    <div className="trading-card">
      <h2>📊 Market Data - {symbol}</h2>
      
      {/* Current Price */}
      <div style={{ 
        background: 'rgba(255, 255, 255, 0.05)', 
        padding: '1.5rem', 
        borderRadius: '8px', 
        marginBottom: '1rem',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
          Current Price
        </div>
        <div style={{ 
          fontSize: '2rem', 
          fontWeight: '600', 
          color: '#ffffff', 
          fontFamily: 'Courier New, monospace'
        }}>
          {formatPrice(price)}
        </div>
        {timestamp && (
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
            Updated: {new Date(timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Market Stats */}
      <div className="market-data-grid">
        <div className="market-data-item">
          <div className="label">Best Bid</div>
          <div className="value">
            {bestBid ? formatPrice(bestBid[0]) : '-'}
          </div>
          {bestBid && (
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              Size: {formatQuantity(bestBid[1])}
            </div>
          )}
        </div>

        <div className="market-data-item">
          <div className="label">Best Ask</div>
          <div className="value">
            {bestAsk ? formatPrice(bestAsk[0]) : '-'}
          </div>
          {bestAsk && (
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              Size: {formatQuantity(bestAsk[1])}
            </div>
          )}
        </div>

        <div className="market-data-item">
          <div className="label">Spread</div>
          <div className="value">
            {spread > 0 ? formatPrice(spread) : '-'}
          </div>
          {spread > 0 && (
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              {spreadPercent.toFixed(3)}%
            </div>
          )}
        </div>

        <div className="market-data-item">
          <div className="label">Mid Price</div>
          <div className="value">
            {bestBid && bestAsk ? formatPrice((bestBid[0] + bestAsk[0]) / 2) : '-'}
          </div>
          {bestBid && bestAsk && (
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              Theoretical
            </div>
          )}
        </div>
      </div>

      {/* Top of Book */}
      <div style={{ marginTop: '1rem' }}>
        <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Top of Book</h3>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          {/* Bids */}
          <div style={{ flex: 1 }}>
            <h4 style={{ fontSize: '0.9rem', color: '#22c55e', marginBottom: '0.5rem' }}>
              🟢 Bids
            </h4>
            {bids.slice(0, 5).map(([price, quantity], index) => (
              <div key={`bid-${index}`} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                padding: '0.25rem', 
                fontSize: '0.8rem',
                fontFamily: 'Courier New, monospace'
              }}>
                <span style={{ color: '#22c55e' }}>{formatPrice(price)}</span>
                <span style={{ color: '#94a3b8' }}>{formatQuantity(quantity)}</span>
              </div>
            ))}
          </div>

          {/* Asks */}
          <div style={{ flex: 1 }}>
            <h4 style={{ fontSize: '0.9rem', color: '#ef4444', marginBottom: '0.5rem' }}>
              🔴 Asks
            </h4>
            {asks.slice(0, 5).map(([price, quantity], index) => (
              <div key={`ask-${index}`} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                padding: '0.25rem', 
                fontSize: '0.8rem',
                fontFamily: 'Courier New, monospace'
              }}>
                <span style={{ color: '#ef4444' }}>{formatPrice(price)}</span>
                <span style={{ color: '#94a3b8' }}>{formatQuantity(quantity)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketData;
