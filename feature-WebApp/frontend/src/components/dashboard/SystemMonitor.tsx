import React, { useEffect, useState } from 'react';

export default function SystemMonitor() {
  const [trades, setTrades] = useState<any[]>([]);
  const [acceptances, setAcceptances] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const t = await fetch('/api/trades').then(r => r.json());
        setTrades(t);
        const a = await fetch('/api/trade_acceptances').then(r => r.json());
        setAcceptances(a);
        const p = await fetch('/api/user_positions?user_id=1').then(r => r.json()); // Example: user_id=1
        setPositions(p);
      } catch (e: any) {
        setError(e.message || 'Error fetching data');
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  return (
    <div style={{ padding: 24, fontFamily: 'monospace', background: '#fff', minHeight: '100vh' }}>
      <h2>System Monitor</h2>
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: 'red' }}>{error}</div>}
      <h3>Recent Trades</h3>
      <pre style={{ background: '#f4f4f4', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>{JSON.stringify(trades, null, 2)}</pre>
      <h3>Recent Trade Acceptances</h3>
      <pre style={{ background: '#f4f4f4', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>{JSON.stringify(acceptances, null, 2)}</pre>
      <h3>User Positions (user_id=1)</h3>
      <pre style={{ background: '#f4f4f4', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>{JSON.stringify(positions, null, 2)}</pre>
    </div>
  );
} 