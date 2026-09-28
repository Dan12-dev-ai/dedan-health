/**
 * UploadProgress — Shows upload progress for image uploads.
 */

import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

export interface UploadProgressProps {
  progress: number;
  filename?: string;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  progress, filename = 'Uploading...',
}) => (
  <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 2 }}>
    <LinearProgress
      variant="determinate"
      value={Math.min(100, Math.max(0, progress))}
      sx={{ flex: 1, height: 6, borderRadius: 3 }}
    />
    <Typography variant="caption" sx={{ minWidth: 40, textAlign: 'right' }}>
      {Math.round(progress)}%
    </Typography>
    {filename && (
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        {filename}
      </Typography>
    )}
  </Box>
);

export default UploadProgress;