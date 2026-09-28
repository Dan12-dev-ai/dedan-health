/**
 * TextComposer — Multimodal text input component.
 *
 * Provides a controlled textarea with character limit,
 * accessibility labels, and keyboard shortcuts.
 */

import React, { useCallback, useRef } from 'react';
import {
  TextField,
  Box,
  Typography,
  IconButton,
} from '@mui/material';
import { Send } from '@mui/icons-material';
import { radius, spacing } from '../../design-system/tokens';

export interface TextComposerProps {
  /** Current text value */
  value: string;
  /** Called on every change */
  onChange: (value: string) => void;
  /** Called when user submits (Enter without Shift) */
  onSubmit: (value: string) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Maximum character count */
  maxLength?: number;
  /** Disabled state */
  disabled?: boolean;
  /** Accessible label */
  label?: string;
  /** Helper text below the input */
  helperText?: string;
}

export const TextComposer: React.FC<TextComposerProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = 'Describe your symptoms...',
  maxLength = 2000,
  disabled = false,
  label = 'Symptom description',
  helperText,
}) => {
  
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (value.trim()) {
          onSubmit(value.trim());
        }
      }
    },
    [value, onSubmit]
  );

  const remaining = maxLength - value.length;
  const isOverLimit = remaining < 0;

  return (
    <Box sx={{ width: '100%' }}>
      <TextField
        label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        multiline
        minRows={6}
        maxRows={8}
        fullWidth
        inputProps={{
          maxLength,
          'aria-label': label,
          'aria-describedby': helperText ? `${label}-helper` : undefined,
          'aria-invalid': isOverLimit || undefined,
        }}
        helperText={
          helperText || (
            <Typography
              id={`${label}-helper`}
              component="span"
              sx={{
                color: isOverLimit ? 'error.main' : 'text.secondary',
                fontSize: '0.75rem',
              }}
            >
              {remaining} characters remaining
            </Typography>
          )
        }
        error={isOverLimit}
        sx={{
          '& .MuiOutlinedInput-root': {
            borderRadius: radius.lg,
          },
        }}
      />
    </Box>
  );
};

export default TextComposer;