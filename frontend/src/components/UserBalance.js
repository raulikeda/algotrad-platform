import React from 'react';

const UserBalance = ({ userInfo }) => {
  if (!userInfo) {
    return (
      <div className="trading-card">
        <h2>💰 Account Balance</h2>
        <div className="balance-grid">
          <div className="balance-item">
            <div className="label">Loading...</div>
            <div className="value">-</div>
          </div>
        </div>
      </div>
    );
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatBTC = (amount) => {
    return `${amount.toFixed(8)} BTC`;
  };

  return (
    <div className="trading-card">
      <h2>💰 Account Balance</h2>
      <div className="balance-grid">
        <div className="balance-item">
          <div className="label">Cash Balance</div>
          <div className="value">{formatCurrency(userInfo.cash_balance)}</div>
        </div>
        <div className="balance-item">
          <div className="label">BTC Balance</div>
          <div 
            className="value" 
            style={{ 
              color: userInfo.asset_balance < 0 ? '#ef4444' : '#10b981',
              fontWeight: userInfo.asset_balance < 0 ? 'bold' : 'normal'
            }}
          >
            {formatBTC(userInfo.asset_balance)}
            {userInfo.asset_balance < 0 && (
              <span style={{ fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                (SHORT)
              </span>
            )}
          </div>
        </div>
        <div className="balance-item">
          <div className="label">Total Value</div>
          <div className="value">{formatCurrency(userInfo.total_value || userInfo.cash_balance)}</div>
        </div>
        <div className="balance-item">
          <div className="label">User ID</div>
          <div className="value" style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>
            {userInfo.user_id.substring(0, 8)}...
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserBalance;
