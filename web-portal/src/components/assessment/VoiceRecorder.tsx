/** Browser SpeechRecognition interface */
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}
interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
}
interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}
interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}
interface SpeechRecognitionConstructor {
  new (): SpeechRecognition;
}
/**
 * VoiceRecorder — Voice-to-text recorder for multimodal assessment.
 */

import React, { useCallback, useRef } from 'react';
import { Box, IconButton, Typography, LinearProgress, Tooltip, Fade } from '@mui/material';
import { Mic, Stop, Delete, VolumeOff } from '@mui/icons-material';
import { radius } from '../../design-system/tokens';
import type { VoiceRecorderState } from './types';

export interface VoiceRecorderProps {
  transcript?: string;
  isRecording: boolean;
  duration: number;
  state: VoiceRecorderState;
  error?: string;
  onStart: () => void;
  onStop: () => void;
  onClear: () => void;
  onCancel: () => void;
  disabled?: boolean;
  label?: string;
}

function getSpeechRecognition(): SpeechRecognition | null {
  if (typeof window === 'undefined') return null;
  const SR = (window as unknown as Record<string, unknown>).SpeechRecognition || (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
  if (!SR) return null;
  return new (SR as SpeechRecognitionConstructor)();
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  transcript, isRecording, duration, state, error,
  onStart, onStop, onClear, onCancel, disabled = false, label = 'Voice input',
}) => {
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const startRecording = useCallback(() => {
    const recognition = getSpeechRecognition();
    if (!recognition) return;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.onend = () => onStop();
    recognition.onerror = () => {};
    try { recognition.start(); recognitionRef.current = recognition; onStart(); } catch { /* ignore */ }
  }, [onStart, onStop]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) { try { recognitionRef.current.stop(); } catch { /* ignore */ } recognitionRef.current = null; }
    onStop();
  }, [onStop]);

  const formatDuration = (secs: number): string => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const isIdle = state === 'idle';
  const isRec = state === 'recording';
  const isStopped = state === 'stopped';
  const isProc = state === 'processing';
  const isReady = state === 'ready';
  const isErr = state === 'error';

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {(isIdle || isStopped || isErr) && (
          <Tooltip title="Start voice recording">
            <span>
              <IconButton onClick={startRecording} disabled={disabled} aria-label="Start voice recording" sx={{ width: 48, height: 48, borderRadius: radius.pill, backgroundColor: 'action.hover', color: 'text.primary' }}>
                <Mic />
              </IconButton>
            </span>
          </Tooltip>
        )}
        {(isRec || isStopped) && (
          <Tooltip title="Stop recording">
            <span>
              <IconButton onClick={stopRecording} disabled={disabled} aria-label="Stop voice recording" sx={{ width: 48, height: 48, borderRadius: radius.pill, backgroundColor: 'error.main', color: '#fff' }}>
                <Stop />
              </IconButton>
            </span>
          </Tooltip>
        )}
        {isRec && (
          <Fade in>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 1 }}>
              <VolumeOff sx={{ color: 'error.main', fontSize: 20 }} />
              <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'error.main' }}>{formatDuration(duration)}</Typography>
            </Box>
          </Fade>
        )}
        {isProc && (
          <Fade in>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 1 }}>
              <LinearProgress sx={{ width: 80, height: 4, borderRadius: radius.pill }} />
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>Processing...</Typography>
            </Box>
          </Fade>
        )}
        {isReady && transcript && (
          <Fade in>
            <Box sx={{ ml: 1, p: 1, borderRadius: radius.md, backgroundColor: 'primary.light', color: 'primary.contrastText', fontSize: '0.8125rem', maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {transcript}
            </Box>
          </Fade>
        )}
        {isReady && transcript && (
          <Tooltip title="Clear voice transcript">
            <IconButton onClick={onClear} disabled={disabled} aria-label="Clear voice transcript" size="small" sx={{ ml: 'auto' }}>
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
        {isErr && (
          <Tooltip title="Cancel voice recording">
            <IconButton onClick={onCancel} disabled={disabled} aria-label="Cancel voice recording" size="small" sx={{ ml: 'auto' }}>
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>
      {error && <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }} role="alert">{error}</Typography>}
      {isIdle && <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>Tap the microphone to speak your symptoms</Typography>}
    </Box>
  );
};

export default VoiceRecorder;
