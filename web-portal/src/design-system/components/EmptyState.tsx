import React from 'react';
import { Box, Typography, Button } from '@mui/material';

export interface EmptyStateProps {
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action, icon }) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center',
      py: 6,
      px: 2,
      color: 'text.secondary',
    }}
  >
    {icon && <Box sx={{ fontSize: 48, mb: 2 }}>{icon}</Box>}
    <Typography variant="h6" color="text.primary" gutterBottom>
      {title}
    </Typography>
    <Typography variant="body2" sx={{ maxWidth: 420, mb: 3 }}>
      {description}
    </Typography>
    {action && (
      <Button variant="contained" onClick={action.onClick}>
        {action.label}
      </Button>
    )}
  </Box>
);
