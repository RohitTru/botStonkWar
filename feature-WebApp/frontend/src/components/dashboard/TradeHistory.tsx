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
      {respondedTrades.length === 0 && <Typography sx={{ color: '#888' }}>No responded trades.</Typography>}
      {respondedTrades.map(trade => (
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