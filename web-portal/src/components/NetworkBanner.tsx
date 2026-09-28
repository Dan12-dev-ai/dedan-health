import React, { useEffect, useState } from 'react';
import { Box, Typography, useTheme } from '@mui/material';
import { Info as InfoIcon, WifiOff as WifiOffIcon } from '@mui/icons-material';

/**
 * Top status banner. Communicates connectivity truthfully:
 *  - online: informational (greenish), auto-dismisses
 *  - offline: persistent amber/red, explains writes are queued locally
 * Never claims "AI processed offline" — only local saving for triage.
 */
export const NetworkBanner: React.FC = () => {
  const [online, setOnline] = useState(() => (typeof navigator !== 'undefined' ? navigator.onLine : true));
  const [visible, setVisible] = useState(true);
  const theme = useTheme();

  useEffect(() => {
    const up = () => { setOnline(true); setVisible(true); };
    const down = () => { setOnline(false); setVisible(true); };
    window.addEventListener('online', up);
    window.addEventListener('offline', down);
    return () => { window.removeEventListener('online', up); window.removeEventListener('offline', down); };
  }, []);

  useEffect(() => {
    if (online && visible) {
      const id = setTimeout(() => setVisible(false), 4000);
      return () => clearTimeout(id);
    }
  }, [online, visible]);

  if (!visible) return null;
  const bg = online ? theme.palette.info.light : theme.palette.warning.light;
  const fg = online ? theme.palette.info.contrastText : theme.palette.getContrastText(theme.palette.warning.light);
  return (
    <Box sx={{
      display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 0.75,
      backgroundColor: bg, color: fg, width: '100%',
    }}>
      {online ? <InfoIcon sx={{ fontSize: 18 }} /> : <WifiOffIcon sx={{ fontSize: 18 }} />}
      <Typography variant="body2" component="span">
        {online ? 'Online — all features available' : 'Offline — your session is saved locally and will sync when you reconnect'}
      </Typography>
    </Box>
  );
};
