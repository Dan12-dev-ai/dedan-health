/**
 * DEDAN-Health — Follow-up
 *
 * Master spec 11 asks for a continuity-of-care experience. Verified constraint:
 * the live v1 backend exposes NO follow-up / reminder / scheduled-message routes.
 *
 * The honest design is therefore:
 *   1. Show the follow-up timeframe the LAST REAL assessment returned
 *      (`TriageResponse.follow_up_timeframe`, read from local history). This is
 *      genuine guidance the patient already received — not a fabricated reminder.
 *   2. State clearly that scheduled reminders and check-ins are not implemented.
 *
 * Nothing on this page is a fake appointment or a fake notification.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Box, Typography, Button, Skeleton, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslations } from '../i18n';
import { offlineStorage } from '../services/offlineStorage';
import { Session, TriageResponse } from '../types';
import { Section, SectionHeading } from '../components/Section';
import { SeverityBadge } from '../design-system/components';
import { colors, radius } from '../design-system/tokens';

function lastTriage(s: Session): TriageResponse | undefined {
  const msgs = s.messages ?? [];
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    if (msgs[i].triage_data) return msgs[i].triage_data;
  }
  if (s.triage_responses?.length) return s.triage_responses[s.triage_responses.length - 1];
  return undefined;
}

function formatStamp(value: string | Date | undefined): string {
  if (!value) return 'Date not recorded';
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return 'Date not recorded';
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export const FollowUpPage: React.FC = () => {
  const { t } = useTranslations();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    offlineStorage
      .getAllSessions()
      .then((s) => setSessions(s as Session[]))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  /** Most recent assessment that actually carried a follow-up timeframe. */
  const latest = useMemo(() => {
    const ordered = sessions
      .slice()
      .sort((a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime());
    for (const s of ordered) {
      const triage = lastTriage(s);
      if (triage) return { session: s, triage };
    }
    return null;
  }, [sessions]);

  return (
    <Section>
      <SectionHeading
        as="h1"
        eyebrow="Continuity"
        title={t('followUp.title')}
        lead="Follow-up is how guidance becomes an outcome. This page shows the follow-up advice from your most recent assessment."
        maxLead={640}
      />

      {loading ? (
        <Box aria-busy="true" sx={{ maxWidth: 720 }}>
          <Skeleton variant="text" width={160} height={18} />
          <Skeleton variant="text" width="70%" height={30} sx={{ mt: 1.5 }} />
          <Skeleton variant="text" width="50%" height={22} sx={{ mt: 1 }} />
        </Box>
      ) : !latest ? (
        /* ---------- No assessment yet: explain, then offer the action ---------- */
        <Box
          sx={{
            border: '1px dashed',
            borderColor: 'divider',
            borderRadius: radius.xl,
            p: { xs: 4, md: 6 },
            maxWidth: 620,
            backgroundColor: 'rgba(46,125,50,0.03)',
          }}
        >
          <Typography component="h2" sx={{ fontSize: '1.25rem', fontWeight: 700, color: 'text.primary', mb: 1 }}>
            {t('followUp.empty')}
          </Typography>
          <Typography sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.secondary', mb: 3 }}>
            {t('followUp.emptyDesc')}
          </Typography>
          <Button
            component={RouterLink}
            to="/assess"
            variant="contained"
            size="large"
            sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
          >
            {t('home.cta')}
          </Button>
        </Box>
      ) : (
        <Box sx={{ maxWidth: 720 }}>
          {/* Real follow-up advice from the recorded assessment. */}
          <Box sx={{ py: 3.5, borderTop: 1, borderTopColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
              <Typography component="h2" sx={{ fontSize: '1.125rem', fontWeight: 650, color: 'text.primary' }}>
                From your most recent assessment
              </Typography>
              <SeverityBadge level={latest.triage.triage_level} />
            </Box>
            <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'text.secondary', mb: 1 }}>
              {formatStamp(latest.session.updated_at || latest.session.created_at)}
            </Typography>

            <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: 'text.primary', mt: 3, mb: 0.5 }}>
              {t('results.followUpLabel')}
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', lineHeight: 1.7, color: 'text.primary' }}>
              {latest.triage.follow_up_timeframe || 'No specific follow-up timeframe was given for this assessment.'}
            </Typography>

            <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: 'text.primary', mt: 4, mb: 0.5 }}>
              {t('results.nextStep')}
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', lineHeight: 1.7, color: 'text.secondary' }}>
              {latest.triage.suggested_next_step}
            </Typography>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 5 }}>
              <Button
                component={RouterLink}
                to={`/history/${latest.session.session_id}`}
                variant="contained"
                size="large"
                sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
              >
                Open full assessment
              </Button>
              <Button
                component={RouterLink}
                to="/assess"
                variant="outlined"
                size="large"
                sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
              >
                {t('results.newAssessment')}
              </Button>
            </Stack>
          </Box>

          {/* Honest scope statement — no fake reminders. */}
          <Box
            sx={{
              mt: 6,
              p: { xs: 3, md: 4 },
              borderRadius: radius.xl,
              border: '1px solid rgba(46,125,50,0.20)',
              backgroundColor: 'rgba(46,125,50,0.05)',
            }}
          >
            <Typography component="h2" sx={{ fontSize: '1rem', fontWeight: 650, color: 'text.primary', mb: 1 }}>
              Scheduled reminders are not available yet
            </Typography>
            <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.75, color: 'text.secondary' }}>
              DEDAN does not currently send scheduled reminders, check-in messages or notifications, and no
              appointments are booked on your behalf. Until this is implemented, follow the advice above and
              seek care if your symptoms change. Your assessments remain available in your history.
            </Typography>
            <Box sx={{ mt: 3 }}>
              <Button
                component={RouterLink}
                to="/help"
                variant="text"
                sx={{ px: 0, color: colors.brand.primary, fontWeight: 600, textDecoration: 'underline', textUnderlineOffset: 4 }}
              >
                When to seek emergency care
              </Button>
            </Box>
          </Box>
        </Box>
      )}
    </Section>
  );
};

export default FollowUpPage;
