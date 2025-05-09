import { Box, Typography, Paper, Button, Chip } from '@mui/material';

export default function TradeHistory({
  activeTrades,
  respondedTrades,
  expiredTrades,
  onAccept,
  onDeny,
  onShowModal,
  expiredLoadMore,
  expiredHasMore
}: {
  activeTrades: any[];
  respondedTrades: any[];
  expiredTrades: any[];
  onAccept: (trade: any) => void;
  onDeny: (trade: any) => void;
  onShowModal: (trade: any) => void;
  expiredLoadMore: () => void;
  expiredHasMore: boolean;
}) {
  // Separate failed trades from respondedTrades
  const failedTrades = respondedTrades.filter(t => t.status === 'FAILED' || t.user_status === 'FAILED');
  const normalResponded = respondedTrades.filter(t => t.status !== 'FAILED' && t.user_status !== 'FAILED');
  return (
    <Box>
      {/* Active */}
      <Typography variant="h6" sx={{ color: '#bdbddd', mb: 1 }}>Active</Typography>
      {activeTrades.length === 0 && <Typography sx={{ color: '#888' }}>No active trade recommendations.</Typography>}
      {activeTrades.map(trade => (
        <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#282a36', borderRadius: 2 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
              <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
              <Typography variant="caption" sx={{ ml: 2 }}>Expires: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
            </Box>
            <Chip label="Active" color="success" />
          </Box>
          <Box mt={1} display="flex" gap={2}>
            <Button variant="contained" size="small" color="success" onClick={() => onAccept(trade)}>Accept</Button>
            <Button variant="outlined" size="small" color="error" onClick={() => onDeny(trade)}>Deny</Button>
          </Box>
        </Paper>
      ))}

      {/* Responded */}
      <Typography variant="h6" sx={{ color: '#bdbddd', mb: 1, mt: 4 }}>Responded</Typography>
      {normalResponded.length === 0 && <Typography sx={{ color: '#888' }}>No responded trades.</Typography>}
      {normalResponded.map(trade => (
        <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#232526', borderRadius: 2 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
              <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
              <Typography variant="caption" sx={{ ml: 2 }}>Expires: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
            </Box>
            <Chip label={trade.user_status} color={trade.user_status === 'ACCEPTED' ? 'success' : 'error'} />
          </Box>
          <Box mt={1}>
            <Typography variant="caption">Allocated: {trade.allocation_amount ? `$${trade.allocation_amount}` : trade.allocation_shares ? `${trade.allocation_shares} shares` : '-'}</Typography>
          </Box>
        </Paper>
      ))}

      {/* Failed */}
      {failedTrades.length > 0 && (
        <>
          <Typography variant="h6" sx={{ color: '#ff6666', mb: 1, mt: 4 }}>Failed</Typography>
          {failedTrades.map(trade => (
            <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#2a2323', borderRadius: 2, border: '1.5px solid #ff6666' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
                  <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
                  <Typography variant="caption" sx={{ ml: 2 }}>Expired: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
                </Box>
                <Chip label="FAILED" color="error" />
              </Box>
              <Box mt={1}>
                <Typography variant="caption" color="#ff6666">This trade was not executed. Your funds have been returned.</Typography>
              </Box>
            </Paper>
          ))}
        </>
      )}

      {/* Expired */}
      <Typography variant="h6" sx={{ color: '#bdbddd', mb: 1, mt: 4 }}>Expired</Typography>
      <Box sx={{ maxHeight: 400, overflowY: 'auto', pr: 1 }}>
        {expiredTrades.length === 0 && <Typography sx={{ color: '#888' }}>No expired trades.</Typography>}
        {expiredTrades.map(trade => (
          <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#232526', borderRadius: 2, opacity: 0.6 }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
                <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
                <Typography variant="caption" sx={{ ml: 2 }}>Expired: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
              </Box>
              <Chip label="Expired" color="default" />
            </Box>
          </Paper>
        ))}
        {expiredHasMore && (
          <Button onClick={expiredLoadMore} fullWidth sx={{ mt: 2 }}>Load More</Button>
        )}
      </Box>
    </Box>
  );
} 