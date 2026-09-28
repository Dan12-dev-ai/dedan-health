import React from 'react';
import { FormControl, FormHelperText, InputLabel, Input, Select, TextField, TextFieldProps } from '@mui/material';
import { radius } from '../tokens';

/** Accessible form field with explicit label, error, and helper text. */
export const FormField: React.FC<{
  label: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  children: React.ReactElement;
}> = ({ label, error, helperText, required, children }) => (
  <FormControl
    fullWidth
    error={!!error}
    sx={{ mb: 2 }}
    aria-invalid={!!error}
    aria-describedby={error ? `${label}-error` : helperText ? `${label}-helper` : undefined}
  >
    {React.cloneElement(children as any, {
      // ensure consistent shape across MUI inputs
      size: 'small',
      ...(children.type === Select ? {} : {}),
    })}
    {!!error && <FormHelperText id={`${label}-error`}>{error}</FormHelperText>}
    {!error && helperText && <FormHelperText id={`${label}-helper`}>{helperText}</FormHelperText>}
  </FormControl>
);

/** Pass-through typed TextField with sensible defaults. */
export const FormTextField: React.FC<TextFieldProps> = (props) => (
  <TextField
    size="small"
    fullWidth
    variant="outlined"
    InputProps={{
      sx: { borderRadius: radius.md },
    }}
    {...props}
  />
);
