import React from 'react';

const TradeHistory = ({ trades }) => {
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

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString();
  };

  // Group trades by date
  const groupedTrades = trades.reduce((groups, trade) => {
    const date = formatDate(trade.timestamp);
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(trade);
    return groups;
  }, {});

  return (
    <div className="trading-card">
      <h2>📈 Trade History</h2>
      
      {trades.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '2rem', 
          color: '#94a3b8',
          fontStyle: 'italic'
        }}>
          No trades yet
        </div>
      ) : (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {Object.entries(groupedTrades).map(([date, dayTrades]) => (
            <div key={date}>
              <div style={{ 
                padding: '0.5rem', 
                background: 'rgba(255,255,255,0.05)', 
                margin: '0.5rem 0', 
                borderRadius: '4px',
                fontSize: '0.9rem',
                fontWeight: '600'
              }}>
                {date}
              </div>
              
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {dayTrades.map((trade) => (
                    <tr key={trade.id}>
                      <td style={{ fontSize: '0.8rem' }}>
                        {formatTime(trade.timestamp)}
                      </td>
                      <td>
                        <span className={trade.side === 'buy' ? 'price-up' : 'price-down'}>
                          {trade.side.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'Courier New, monospace' }}>
                        {formatQuantity(trade.quantity)}
                      </td>
                      <td style={{ fontFamily: 'Courier New, monospace' }}>
                        {formatPrice(trade.price)}
                      </td>
                      <td style={{ fontFamily: 'Courier New, monospace', fontWeight: '600' }}>
                        {formatPrice(trade.quantity * trade.price)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
          
          {/* Summary */}
          {trades.length > 0 && (
            <div style={{ 
              marginTop: '1rem', 
              padding: '1rem', 
              background: 'rgba(255,255,255,0.05)', 
              borderRadius: '8px'
            }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem' }}>Summary</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem' }}>
                <div>Total Trades: <strong>{trades.length}</strong></div>
                <div>
                  Total Volume: <strong>
                    {formatQuantity(trades.reduce((sum, trade) => sum + trade.quantity, 0))} BTC
                  </strong>
                </div>
                <div>
                  Buys: <strong>{trades.filter(t => t.side === 'buy').length}</strong>
                </div>
                <div>
                  Sells: <strong>{trades.filter(t => t.side === 'sell').length}</strong>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TradeHistory;
