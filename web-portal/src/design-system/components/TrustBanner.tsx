import React from 'react';
import { Box, Alert, AlertTitle, Typography, Link } from '@mui/material';
import { ShieldCheckIcon } from './icons';

/**
 * DEDAN trust/disclaimer banner. No unsupported certification claims.
 * Shows: privacy note, AI-transparency note, disclaimer.
 */
export interface TrustBannerProps {
  tone?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
}

export const TrustBanner: React.FC<TrustBannerProps> = ({
  tone = 'info',
  title,
  children,
}) => (
  <Alert
    severity={tone}
    icon={false}
    sx={{
      border: 'none',
      borderRadius: 2,
      background: 'var(--dedan-color-surface, rgba(243, 244, 246, 0.7))',
    }}
  >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
      <ShieldCheckIcon sx={{ fontSize: 20, mt: 0.25, color: 'inherit' }} />
      <Box sx={{ flex: 1 }}>
        {title && <AlertTitle sx={{ fontWeight: 600 }}>{title}</AlertTitle>}
        <Typography variant="body2">{children}</Typography>
      </Box>
    </Box>
  </Alert>
);
