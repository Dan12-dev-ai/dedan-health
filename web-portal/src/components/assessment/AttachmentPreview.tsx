/**
 * AttachmentPreview — Image preview with remove and replace actions.
 *
 * Displays a selected image thumbnail with:
 * - remove button
 * - replace button
 * - accessibility labels
 */

import React from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  Typography,
} from '@mui/material';
import { Close, Refresh } from '@mui/icons-material';
import { radius } from '../../design-system/tokens';

export interface AttachmentPreviewProps {
  /** Preview URL (data URL or object URL) */
  preview: string;
  /** File name */
  filename: string;
  /** Called when user removes the image */
  onRemove: () => void;
  /** Called when user wants to replace the image */
  onReplace: () => void;
  /** Disabled state */
  disabled?: boolean;
}

export const AttachmentPreview: React.FC<AttachmentPreviewProps> = ({
  preview, filename, onRemove, onReplace, disabled = false,
}) => (
  <Box
    sx={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 1,
      p: 1,
      borderRadius: radius.lg,
      backgroundColor: 'background.paper',
      border: '1px solid',
      borderColor: 'divider',
      maxWidth: '100%',
    }}
  >
    <Box
      component="img"
      src={preview}
      alt={`Preview: ${filename}`}
      sx={{
        width: 48,
        height: 48,
        objectFit: 'cover',
        borderRadius: radius.sm,
        flexShrink: 0,
      }}
    />
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Typography
        variant="caption"
        sx={{
          display: 'block',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {filename}
      </Typography>
    </Box>
    <Tooltip title="Replace image">
      <span>
        <IconButton onClick={onReplace} disabled={disabled} aria-label="Replace image" size="small">
          <Refresh fontSize="small" />
        </IconButton>
      </span>
    </Tooltip>
    <Tooltip title="Remove image">
      <span>
        <IconButton onClick={onRemove} disabled={disabled} aria-label="Remove image" size="small">
          <Close fontSize="small" />
        </IconButton>
      </span>
    </Tooltip>
  </Box>
);

export default AttachmentPreview;