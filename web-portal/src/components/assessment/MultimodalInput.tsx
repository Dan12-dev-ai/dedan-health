/**
 * MultimodalInput — Unified text + image + voice input component.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Box, Button, CircularProgress, Alert, Chip } from '@mui/material';
import { Send as SendIcon, Image as ImageIcon, Mic as MicIcon } from '@mui/icons-material';
import { radius } from '../../design-system/tokens';
import { TextComposer } from './TextComposer';
import { VoiceRecorder } from './VoiceRecorder';
import { AttachmentPreview } from './AttachmentPreview';
import { UploadProgress } from './UploadProgress';
import { validateImageFile, deleteImage } from '../../services/multimodalService';
import type { MultimodalInputState, VoiceRecorderState } from './types';
import type { PatientProfile } from '../../types';

export interface MultimodalInputProps {
  value: MultimodalInputState;
  patient: PatientProfile;
  sessionId?: string;
  onSubmit: (request: { text: string; voiceTranscript?: string; image?: File; imagePreview?: string; uploadedImageId?: string; }) => void;
  onChange: (value: Partial<MultimodalInputState>) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export const MultimodalInput: React.FC<MultimodalInputProps> = ({
  value, patient, sessionId, onSubmit, onChange,
  disabled = false, loading = false, placeholder, maxLength = 2000,
}) => {
  const { text, image, imagePreview, uploadedImageId, voiceTranscript, isRecording, isUploading, uploadProgress, error } = value;
  const [voiceState, setVoiceState] = useState<VoiceRecorderState>('idle');
  const [voiceDuration, setVoiceDuration] = useState(0);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current); }, []);

  const handleImageSelect = useCallback(async (file: File) => {
    const validation = validateImageFile(file);
    if (!validation.valid) { onChange({ error: validation.error }); return; }
    if (uploadedImageId) { try { await deleteImage(uploadedImageId); } catch { /* ignore */ } }
    const preview = URL.createObjectURL(file);
    onChange({ image: file, imagePreview: preview, uploadedImageId: undefined, error: undefined });
  }, [uploadedImageId, onChange]);

  const handleImageRemove = useCallback(() => {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    if (uploadedImageId) { deleteImage(uploadedImageId).catch(() => {}); }
    onChange({ image: undefined, imagePreview: undefined, uploadedImageId: undefined });
  }, [imagePreview, uploadedImageId, onChange]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleImageSelect(file);
    if (e.target) e.target.value = '';
  }, [handleImageSelect]);

  const handleVoiceStart = useCallback(() => { setVoiceState('recording'); setVoiceDuration(0); setVoiceError(null); timerRef.current = setInterval(() => setVoiceDuration((d) => d + 1), 1000); }, []);
  const handleVoiceStop = useCallback(() => { if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; } setVoiceState('stopped'); }, []);
  const handleVoiceClear = useCallback(() => { onChange({ voiceTranscript: undefined }); setVoiceState('idle'); setVoiceDuration(0); setVoiceError(null); }, [onChange]);
  const handleVoiceCancel = useCallback(() => { onChange({ voiceTranscript: undefined }); setVoiceState('idle'); setVoiceDuration(0); setVoiceError(null); }, [onChange]);

  const handleSubmit = useCallback(() => {
    if (!text.trim() && !voiceTranscript && !image && !uploadedImageId) return;
    if (loading) return;
    onSubmit({ text: text.trim(), voiceTranscript: voiceTranscript || undefined, image: image || undefined, imagePreview: imagePreview || undefined, uploadedImageId: uploadedImageId || undefined });
  }, [text, voiceTranscript, image, imagePreview, uploadedImageId, loading, onSubmit]);

  const canSubmit = !!(text.trim() || voiceTranscript || image || uploadedImageId);

  return (
    <Box sx={{ width: '100%' }}>
      {error && <Alert severity="error" sx={{ mb: 2, borderRadius: radius.lg }}>{error}</Alert>}
      {imagePreview && (
        <Box sx={{ mb: 2 }}>
          <AttachmentPreview preview={imagePreview} filename={image?.name || 'Image'} onRemove={handleImageRemove} onReplace={() => fileInputRef.current?.click()} disabled={disabled || loading} />
        </Box>
      )}
      {isUploading && (<Box sx={{ mb: 2 }}><UploadProgress progress={uploadProgress} /></Box>)}
      <Box sx={{ mb: 2 }}>
        <VoiceRecorder transcript={voiceTranscript} isRecording={isRecording} duration={voiceDuration} state={voiceState} error={voiceError || undefined} onStart={handleVoiceStart} onStop={handleVoiceStop} onClear={handleVoiceClear} onCancel={handleVoiceCancel} disabled={disabled || loading} />
      </Box>
      <Box sx={{ mb: 2 }}>
        <TextComposer value={text} onChange={(v) => onChange({ text: v })} onSubmit={handleSubmit} placeholder={placeholder} maxLength={maxLength} disabled={disabled || loading} helperText={voiceTranscript ? `Voice: ${voiceTranscript.slice(0, 80)}${voiceTranscript.length > 80 ? '...' : ''}` : undefined} />
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif" onChange={handleFileChange} style={{ display: 'none' }} aria-hidden="true" disabled={disabled || loading} />
        <Button variant="outlined" startIcon={<ImageIcon />} onClick={() => fileInputRef.current?.click()} disabled={disabled || loading || !!image} aria-label="Attach image" sx={{ borderRadius: radius.pill, textTransform: 'none' }}>Image</Button>
        <Button variant="outlined" startIcon={<MicIcon />} disabled sx={{ borderRadius: radius.pill, textTransform: 'none', opacity: 0.5 }}>Voice</Button>
        <Button variant="contained" color="primary" endIcon={loading ? <CircularProgress size={16} color="inherit" /> : <SendIcon />} onClick={handleSubmit} disabled={!canSubmit || disabled || loading} aria-label="Submit assessment" sx={{ borderRadius: radius.pill, textTransform: 'none', ml: 'auto', minWidth: 120 }}>{loading ? 'Analyzing...' : 'Analyze'}</Button>
      </Box>
      {voiceTranscript && (
        <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label={`Voice: ${voiceTranscript.slice(0, 60)}${voiceTranscript.length > 60 ? '...' : ''}`} size="small" variant="outlined" onDelete={handleVoiceClear}  />
        </Box>
      )}
    </Box>
  );
};

export default MultimodalInput;
