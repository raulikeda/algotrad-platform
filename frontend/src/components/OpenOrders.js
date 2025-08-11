import React, { useState } from 'react';

const OpenOrders = ({ orders, onCancelOrder, onUpdateOrder }) => {
  const [editingOrder, setEditingOrder] = useState(null);
  const [editData, setEditData] = useState({ price: '', quantity: '' });

  const handleEdit = (order) => {
    setEditingOrder(order.id);
    setEditData({
      price: order.price ? order.price.toString() : '',
      quantity: order.quantity.toString()
    });
  };

  const handleCancelEdit = () => {
    setEditingOrder(null);
    setEditData({ price: '', quantity: '' });
  };

  const handleUpdate = async (orderId) => {
    try {
      const updatePayload = {};
      if (editData.price && parseFloat(editData.price) > 0) {
        updatePayload.price = parseFloat(editData.price);
      }
      if (editData.quantity && parseFloat(editData.quantity) > 0) {
        updatePayload.quantity = parseFloat(editData.quantity);
      }

      await onUpdateOrder(orderId, updatePayload);
      setEditingOrder(null);
      setEditData({ price: '', quantity: '' });
    } catch (error) {
      console.error('Failed to update order:', error);
    }
  };

  const formatPrice = (price) => {
    if (!price) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatQuantity = (quantity) => {
    return quantity ? quantity.toFixed(8) : '0';
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return '#3b82f6';
      case 'partial': return '#f59e0b';
      case 'filled': return '#10b981';
      case 'cancelled': return '#6b7280';
      default: return '#94a3b8';
    }
  };

  // Sort orders by timestamp in descending order (newest first)
  const sortedOrders = [...orders].sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp);
  });

  return (
    <div className="trading-card">
      <h2>📋 My Orders</h2>
      
      {orders.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '2rem', 
          color: '#94a3b8',
          fontStyle: 'italic'
        }}>
          No open orders
        </div>
      ) : (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Side</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedOrders.map((order) => (
                <tr key={order.id}>
                  <td style={{ fontSize: '0.8rem' }}>
                    {formatTime(order.timestamp)}
                  </td>
                  <td>
                    <span style={{ 
                      padding: '0.2rem 0.5rem', 
                      borderRadius: '4px', 
                      fontSize: '0.8rem',
                      background: order.order_type === 'market' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                      color: order.order_type === 'market' ? '#3b82f6' : '#10b981'
                    }}>
                      {order.order_type.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={order.side === 'buy' ? 'price-up' : 'price-down'}>
                      {order.side.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {editingOrder === order.id ? (
                      <input
                        type="number"
                        value={editData.quantity}
                        onChange={(e) => setEditData(prev => ({ ...prev, quantity: e.target.value }))}
                        style={{
                          width: '80px',
                          padding: '0.2rem',
                          border: '1px solid #ccc',
                          borderRadius: '4px',
                          background: '#fff',
                          color: '#000',
                          fontSize: '0.8rem'
                        }}
                        step="0.01"
                        min="0"
                      />
                    ) : (
                      <span style={{ fontFamily: 'Courier New, monospace' }}>
                        {formatQuantity(order.remaining_quantity)} / {formatQuantity(order.quantity)}
                      </span>
                    )}
                  </td>
                  <td>
                    {editingOrder === order.id && order.order_type === 'limit' ? (
                      <input
                        type="number"
                        value={editData.price}
                        onChange={(e) => setEditData(prev => ({ ...prev, price: e.target.value }))}
                        style={{
                          width: '100px',
                          padding: '0.2rem',
                          border: '1px solid #ccc',
                          borderRadius: '4px',
                          background: '#fff',
                          color: '#000',
                          fontSize: '0.8rem'
                        }}
                        step="10"
                        min="0"
                      />
                    ) : (
                      <span style={{ fontFamily: 'Courier New, monospace' }}>
                        {formatPrice(order.price)}
                      </span>
                    )}
                  </td>
                  <td>
                    <span style={{ 
                      padding: '0.2rem 0.5rem', 
                      borderRadius: '4px', 
                      fontSize: '0.8rem',
                      background: `${getStatusColor(order.status)}20`,
                      color: getStatusColor(order.status)
                    }}>
                      {order.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {editingOrder === order.id ? (
                        <>
                          <button
                            onClick={() => handleUpdate(order.id)}
                            className="btn btn-primary btn-small"
                          >
                            ✓
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="btn btn-warning btn-small"
                          >
                            ✗
                          </button>
                        </>
                      ) : order.status === 'pending' ? (
                        <>
                          <button
                            onClick={() => handleEdit(order)}
                            className="btn btn-primary btn-small"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={() => onCancelOrder(order.id)}
                            className="btn btn-danger btn-small"
                          >
                            ❌
                          </button>
                        </>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default OpenOrders;
