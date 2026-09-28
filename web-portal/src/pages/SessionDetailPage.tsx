/**
 * DEDAN-Health — Assessment detail
 *
 * Reads the LIVE route `GET /dedan/v1/session/{session_id}` first. The v1
 * backend keeps sessions in memory, so a restart or a different device will
 * return 404. In that case — and only then — we fall back to the session saved
 * locally by `offlineStorage`.
 *
 * This is stated in the UI (`source` line) rather than silently presented as if
 * it came from the server. The previous build's comment claimed a local
 * fallback existed, but the code never performed one.
 *
 * The rendered guidance reuses `ResultsCard` so a historical result has exactly
 * the same safety hierarchy as a live one.
 */
import React, { useEffect, useState } from 'react';
import { Box, Typography, Button, Skeleton, Stack } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { SeverityBadge } from '../design-system/components';
import { useTranslations } from '../i18n';
import { getSession } from '../services';
import { offlineStorage } from '../services/offlineStorage';
import { TriageSession, TriageResponse } from '../types';
import { ResultsCard } from './ResultsPage';
import { Section } from '../components/Section';
import { radius } from '../design-system/tokens';

type Source = 'server' | 'device';

function lastTriageOf(s: TriageSession): TriageResponse | undefined {
  if (s.triage_responses?.length) return s.triage_responses[s.triage_responses.length - 1];
  return undefined;
}

function formatStamp(value: string | Date | undefined): string {
  if (!value) return 'Date not recorded';
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return 'Date not recorded';
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

const DetailSkeleton: React.FC = () => (
  <Box aria-busy="true" sx={{ maxWidth: 720 }}>
    <Typography sx={{ position: 'absolute', left: -10000, fontSize: '0.875rem' }}>
      Loading assessment
    </Typography>
    <Skeleton variant="text" width={180} height={18} />
    <Skeleton variant="text" width="65%" height={38} sx={{ mt: 1.5 }} />
    <Skeleton variant="rounded" height={160} sx={{ mt: 3, borderRadius: 2 }} />
    <Skeleton variant="text" width="80%" height={22} sx={{ mt: 4 }} />
    <Skeleton variant="text" width="55%" height={22} sx={{ mt: 1 }} />
  </Box>
);

export const SessionDetailPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { t } = useTranslations();
  const navigate = useNavigate();

  const [data, setData] = useState<TriageSession | null>(null);
  const [source, setSource] = useState<Source | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      return;
    }
    let cancelled = false;

    (async () => {
      // 1) Preferred source: the live backend.
      const res = await getSession(sessionId);
      if (cancelled) return;

      if (res.ok) {
        setData(res.data);
        setSource('server');
        setServerError(null);
        setLoading(false);
        return;
      }

      setServerError(res.message);

      // 2) Fallback: the copy saved on this device.
      const local = await offlineStorage.getSession(sessionId).catch(() => null);
      if (cancelled) return;

      if (local?.triage_responses?.length) {
        setData({
          session_id: local.session_id,
          patient_profile: local.patient_profile as TriageSession['patient_profile'],
          symptoms_history: [],
          triage_responses: local.triage_responses as TriageResponse[],
          created_at: String(local.created_at),
          updated_at: String(local.updated_at),
          status: 'local',
        });
        setSource('device');
      }
      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  if (loading) {
    return (
      <Section size="tight">
        <DetailSkeleton />
      </Section>
    );
  }

  const last = data ? lastTriageOf(data) : undefined;

  if (!data || !last) {
    return (
      <Section size="tight">
        <Box sx={{ maxWidth: 620 }}>
          <Typography component="h1" sx={{ fontSize: { xs: '1.5rem', md: '2rem' }, fontWeight: 700, letterSpacing: '-0.025em', color: 'text.primary', mb: 2 }}>
            This assessment is not available
          </Typography>
          <Typography sx={{ fontSize: '1rem', lineHeight: 1.75, color: 'text.secondary', mb: 4 }}>
            {serverError
              ? 'The DEDAN service could not return this session, and there is no copy saved on this device. Assessments are kept in the service memory, so older entries may no longer be retrievable.'
              : 'There is no record of this assessment on this device or on the service.'}
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button
              onClick={() => navigate('/history')}
              variant="contained"
              size="large"
              sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
            >
              {t('nav.history')}
            </Button>
            <Button
              onClick={() => navigate('/assess')}
              variant="outlined"
              size="large"
              sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
            >
              {t('results.newAssessment')}
            </Button>
          </Stack>
        </Box>
      </Section>
    );
  }

  return (
    <Section size="tight">
      <Box sx={{ maxWidth: 720 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <Typography
            component="p"
            sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'primary.main' }}
          >
            {t('results.yourGuidance')}
          </Typography>
          <SeverityBadge level={last.triage_level} />
        </Box>

        <Typography component="h1" sx={{ fontSize: { xs: '1.5rem', md: '2rem' }, lineHeight: 1.2, fontWeight: 700, letterSpacing: '-0.025em', color: 'text.primary' }}>
          {formatStamp(data.updated_at || data.created_at)}
        </Typography>

        <Typography sx={{ mt: 1, mb: 4, fontSize: '0.875rem', color: 'text.secondary' }}>
          {source === 'server'
            ? 'Retrieved from the DEDAN service.'
            : 'Retrieved from this device. The service no longer holds this session.'}
        </Typography>

        {data.patient_profile && (
          <Box
            sx={{
              mb: 5,
              p: 3,
              borderRadius: radius.lg,
              border: '1px solid',
              borderColor: 'divider',
              backgroundColor: 'rgba(46,125,50,0.03)',
            }}
          >
            <Typography component="h2" sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 1 }}>
              Patient context at the time
            </Typography>
            <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
              Age {data.patient_profile.age} · {data.patient_profile.sex}
              {data.patient_profile.pregnancy_status ? ' · pregnant' : ''}
              {data.patient_profile.chronic_conditions?.length
                ? ` · conditions: ${data.patient_profile.chronic_conditions.join(', ')}`
                : ''}
            </Typography>
          </Box>
        )}

        <ResultsCard response={last} onNew={() => navigate('/assess')} />

        <Box sx={{ mt: 6 }}>
          <Button
            onClick={() => navigate('/history')}
            variant="outlined"
            sx={{ borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary', px: 3 }}
          >
            Back to history
          </Button>
        </Box>
      </Box>
    </Section>
  );
};

export default SessionDetailPage;
