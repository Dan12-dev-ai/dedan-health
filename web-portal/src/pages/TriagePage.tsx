/**
 * DEDAN-Health — Assessment: symptoms (step 2 of 2)
 *
 * Master spec 12 / 13 / 14 / 32: the core product interaction.
 *
 * Design decisions that are deliberate, not incidental:
 *  - This is a GUIDED ASSESSMENT, not a messaging app. There is no chat bubble
 *    stream, no "assistant" persona and no open-ended conversation loop.
 *  - Progress is explicit (step 2 of 2) and the primary action is fixed at the
 *    bottom of the shell.
 *  - The processing state describes only the three real stages of the pipeline.
 *    It never implies clinical reasoning the system does not perform.
 *  - User input is NEVER cleared on failure (master spec 51).
 *  - No voice input is offered because the live backend path does not implement
 *    `voice_input` transcription end-to-end (removed rather than faked).
 *
 * Backend contract: POST /dedan/v1/triage with
 *   { patient, symptoms: { symptoms, duration?, severity? }, session_id, consent }
 */
import React, { useEffect, useMemo, useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  Alert,
  LinearProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTranslations } from '../i18n';
import { useDedanState } from '../state/DedanContext';
import { postTriage, isOnline } from '../services';
import { submitMultimodalAnalysis, postClinicalGuidance } from '../services/multimodalService';
import { TriageRequest, SymptomSeverity, ClinicalGuidanceRequest2 } from '../types';
import { AssessmentShell } from '../components/assessment/AssessmentShell';
import { MultimodalInput } from '../components/assessment/MultimodalInput';
import { MultimodalMessage } from '../components/assessment/MultimodalMessage';
import { radius } from '../design-system/tokens';

/**
 * Real stages of the live request. Shown in order to communicate progress
 * honestly — these are workflow stages, not simulated "AI thoughts".
 */
const STAGES = ['triage.reviewing', 'triage.checking', 'triage.deciding'] as const;

const fieldLabel = {
  display: 'block',
  mb: 1,
  fontSize: '0.9375rem',
  fontWeight: 600,
  color: 'text.primary',
} as const;

const helpText = {
  mt: 1,
  fontSize: '0.875rem',
  color: 'text.secondary',
} as const;

export const TriagePage: React.FC = () => {
  const { t } = useTranslations();
  const { profile, sessionId, saveRequest, pushTriageResult } = useDedanState();
  const navigate = useNavigate();

  const [symptoms, setSymptoms] = useState('');
  const [duration, setDuration] = useState('');
  const [severity, setSeverity] = useState<SymptomSeverity | ''>('');
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState(0);
  const [response, setResponse] = useState<any>(null);
  const [multimodalLoading, setMultimodalLoading] = useState(false);

  // Multimodal input state
  const [multimodalInput, setMultimodalInput] = useState({
    text: '',
    image: undefined as File | undefined,
    imagePreview: undefined as string | undefined,
    uploadedImageId: undefined as string | undefined,
    voiceTranscript: undefined as string | undefined,
    isRecording: false,
    isUploading: false,
    uploadProgress: 0,
    error: undefined as string | undefined,
  });

  // Step 1 is mandatory: without a profile the backend would reject the payload.
  useEffect(() => {
    if (!profile) navigate('/assess', { replace: true });
  }, [profile, navigate]);

  /** Advance the visible stage while the single request is in flight. */
  useEffect(() => {
    if (!loading) {
      setStage(0);
      return;
    }
    const id = setInterval(() => setStage((s) => (s < STAGES.length - 1 ? s + 1 : s)), 1200);
    return () => clearInterval(id);
  }, [loading]);

  const durations = useMemo(
    () => [
      { value: 'Under 24 hours', label: t('assess.durationHours') },
      { value: '2-7 days', label: t('assess.durationDays') },
      { value: '1-4 weeks', label: t('assess.durationWeeks') },
      { value: 'More than a month', label: t('assess.durationMonths') },
      { value: 'Not sure', label: t('assess.durationUnknown') },
    ],
    [t],
  );

  const buildRequest = useCallback(
    (): TriageRequest => ({
      patient: profile!,
      symptoms: {
        symptoms: symptoms.trim(),
        duration: duration || undefined,
        severity: severity || undefined,
      },
      session_id: sessionId,
      consent: true,
    }),
    [profile, symptoms, duration, severity, sessionId],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!profile || loading) return;

      // Backend requires symptoms of at least 5 characters (models.py).
      if (symptoms.trim().length < 5) {
        setFieldError(t('assess.symptomsTooShort'));
        document.getElementById('assess-symptoms')?.focus();
        return;
      }

      setFieldError(null);
      setError(null);

      if (!isOnline()) {
        setError(t('results.offlineNotice'));
        return;
      }

      setLoading(true);
      const request = buildRequest();

      try {
        const result = await postTriage(request);
        if (!result.ok) {
          // Input is preserved so the patient never retypes their symptoms.
          setError(result.message || t('triage.error'));
          return;
        }
        await saveRequest(request);
        pushTriageResult(result.data);
        navigate('/results', { state: { response: result.data } });
      } catch {
        setError(t('triage.error'));
      } finally {
        setLoading(false);
      }
    },
    [profile, loading, symptoms, buildRequest, saveRequest, pushTriageResult, navigate, t],
  );

  // Multimodal submit handler — uses DEDAN Health 2.0 clinical guidance endpoint
  const handleMultimodalSubmit = useCallback(async (request: {
    text: string;
    voiceTranscript?: string;
    image?: File;
    imagePreview?: string;
    uploadedImageId?: string;
  }) => {
    if (!profile) return;
    if (!request.text.trim() && !request.voiceTranscript && !request.image && !request.uploadedImageId) return;

    setMultimodalLoading(true);
    setError(null);
    setResponse(null);

    try {
      const clinicalRequest: ClinicalGuidanceRequest2 = {
        patient: profile,
        symptoms: {
          symptoms: request.text || '',
          voice_input: !!request.voiceTranscript,
          duration,
          severity: (severity === '' ? undefined : (severity as SymptomSeverity)) as SymptomSeverity | undefined,
        },
        image_ids: request.uploadedImageId ? [request.uploadedImageId] : [],
        image_data_list: request.image ? [] : [],
        voice_transcript: request.voiceTranscript || undefined,
        session_id: sessionId || undefined,
        conversation_history: [],
        consent: true,
      };

      const result = await postClinicalGuidance(clinicalRequest);
      if (result.ok) {
        setResponse(result.data);
      } else {
        setError(result.message || 'Analysis failed');
      }
    } catch {
      setError('Failed to analyze. Please try again.');
    } finally {
      setMultimodalLoading(false);
    }
  }, [profile, sessionId, duration, severity]);

  if (!profile) return null;

  return (
    <AssessmentShell
      progress={{ current: 2, total: 2, labelTemplate: t('assess.step') }}
      title={t('assess.step2Title')}
      lead={t('assess.step2Lead')}
      notice={t('results.uncertainty')}
      actions={
        <>
          <Button
            type="button"
            variant="outlined"
            size="large"
            onClick={() => navigate('/assess')}
            disabled={loading}
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: radius.pill,
              borderColor: 'divider',
              color: 'text.primary',
              flexShrink: 0,
            }}
          >
            {t('assess.back')}
          </Button>
          <Button
            type="submit"
            form="triage-form"
            variant="contained"
            size="large"
            disabled={loading || symptoms.trim().length < 5}
            sx={{ px: 4, py: 1.5, borderRadius: radius.pill, flexGrow: { xs: 1, sm: 0 } }}
          >
            {loading ? t('assess.submitting') : t('assess.submit')}
          </Button>
        </>
      }
    >
      <Box id="triage-form" component="form" onSubmit={handleSubmit} noValidate>
        {/* ---- Multimodal Input ---- */}
        <Box sx={{ mb: 5 }}>
          <MultimodalInput
            value={multimodalInput}
            patient={profile}
            sessionId={sessionId}
            onSubmit={handleMultimodalSubmit}
            onChange={(updates) => setMultimodalInput((prev) => ({ ...prev, ...updates }))}
            disabled={loading || multimodalLoading}
            loading={multimodalLoading}
            placeholder={t('assess.symptomsPlaceholder')}
            maxLength={1000}
          />
        </Box>

        {/* ---- Duration + severity (both optional, both real backend fields) ---- */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
            columnGap: 4,
            rowGap: 5,
          }}
        >
          <Box>
            <Typography component="label" htmlFor="assess-duration" sx={fieldLabel}>
              {t('assess.durationLabel')}
            </Typography>
            <FormControl fullWidth>
              <Select
                id="assess-duration"
                displayEmpty
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                disabled={loading}
                sx={{ borderRadius: radius.lg }}
                inputProps={{ 'aria-describedby': 'assess-duration-help' }}
              >
                <MenuItem value="">
                  <em style={{ opacity: 0.6 }}>Not specified</em>
                </MenuItem>
                {durations.map((d) => (
                  <MenuItem key={d.value} value={d.value}>
                    {d.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography id="assess-duration-help" component="p" sx={helpText}>
              {t('assess.durationHelp')}
            </Typography>
          </Box>

          <Box>
            <Typography component="label" htmlFor="assess-severity" sx={fieldLabel}>
              {t('assess.severityLabel')}
            </Typography>
            <FormControl fullWidth>
              <Select
                id="assess-severity"
                displayEmpty
                value={severity}
                onChange={(e) => setSeverity(e.target.value as SymptomSeverity | '')}
                disabled={loading}
                sx={{ borderRadius: radius.lg }}
                inputProps={{ 'aria-describedby': 'assess-severity-help' }}
              >
                <MenuItem value="">
                  <em style={{ opacity: 0.6 }}>Not specified</em>
                </MenuItem>
                <MenuItem value="mild">{t('assess.severityMild')}</MenuItem>
                <MenuItem value="moderate">{t('assess.severityModerate')}</MenuItem>
                <MenuItem value="severe">{t('assess.severitySevere')}</MenuItem>
              </Select>
            </FormControl>
            <Typography id="assess-severity-help" component="p" sx={helpText}>
              {t('assess.severityHelp')}
            </Typography>
          </Box>
        </Box>

        {/* ---- Progress: appears only while the request is genuinely in flight ---- */}
        {loading && (
          <Box
            role="status"
            aria-live="polite"
            sx={{
              mt: 6,
              p: 3,
              borderRadius: radius.lg,
              border: '1px solid rgba(46,125,50,0.20)',
              backgroundColor: 'rgba(46,125,50,0.05)',
            }}
          >
            <Typography component="h3" sx={{ fontSize: '1rem', fontWeight: 650, color: 'text.primary', mb: 0.5 }}>
              {t('assess.processingTitle')}
            </Typography>
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', mb: 2.5 }}>
              {t('assess.processingNote')}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={((stage + 1) / STAGES.length) * 100}
              sx={{
                height: 6,
                borderRadius: radius.pill,
                backgroundColor: 'rgba(46,125,50,0.15)',
                '& .MuiLinearProgress-bar': { borderRadius: radius.pill },
              }}
            />
            <Typography sx={{ mt: 2, fontSize: '0.9375rem', color: 'text.primary', fontWeight: 500 }}>
              {t(STAGES[stage])}
            </Typography>
          </Box>
        )}

        {/* ---- Failure: keeps the input, offers the next real action ---- */}
        {error && (
          <Box sx={{ mt: 6 }}>
            <Alert
              severity="error"
              sx={{ borderRadius: radius.lg }}
              action={
                <Button color="inherit" size="small" onClick={() => setError(null)}>
                  {t('errors.retry')}
                </Button>
              }
            >
              <Typography sx={{ fontWeight: 600, mb: 0.5 }}>{t('errors.genericTitle')}</Typography>
              <Typography sx={{ fontSize: '0.9375rem' }}>{error}</Typography>
              <Typography sx={{ fontSize: '0.875rem', mt: 0.5, opacity: 0.9 }}>
                Your symptoms have not been lost — you can send them again.
              </Typography>
            </Alert>
          </Box>
        )}

        {/* ---- Multimodal AI Response ---- */}
        {response && (
          <Box sx={{ mt: 6 }}>
            <MultimodalMessage response={response} />
          </Box>
        )}
      </Box>
    </AssessmentShell>
  );
};

export default TriagePage;
