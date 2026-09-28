/**
 * DEDAN-Health — Assessment history
 *
 * Master spec 10 / 33: a TIMELINE, not a repeated stack of cards.
 *
 * Data source (important, and stated honestly in the UI): history is read from
 * `offlineStorage` (IndexedDB/`localStorage` on this device). It is a LOCAL
 * record. The live v1 backend can return a session by id
 * (`GET /dedan/v1/session/{id}`) but exposes no "list all my sessions" route,
 * so this page does not claim server-side history.
 *
 * States implemented: loading (skeleton) / empty / error-free list.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Box, Typography, Button, Skeleton } from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { SeverityBadge } from '../design-system/components';
import { useTranslations } from '../i18n';
import { offlineStorage } from '../services/offlineStorage';
import { Session, TriageResponse, TriageLevel } from '../types';
import { Section, SectionHeading } from '../components/Section';
import { colors, radius } from '../design-system/tokens';

/** Latest triage result contained in a locally stored session. */
function lastTriage(s: Session): TriageResponse | undefined {
  const msgs = s.messages ?? [];
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    if (msgs[i].triage_data) return msgs[i].triage_data;
  }
  if (s.triage_responses?.length) return s.triage_responses[s.triage_responses.length - 1];
  return undefined;
}

const levelOf = (s: Session): TriageLevel => lastTriage(s)?.triage_level ?? 'routine';

/** Format a stored timestamp defensively — never render "Invalid Date". */
function formatStamp(value: string | Date | undefined): string {
  if (!value) return 'Date not recorded';
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return 'Date not recorded';
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

const HistorySkeleton: React.FC = () => (
  <Box aria-busy="true" aria-live="polite">
    <Typography sx={{ position: 'absolute', left: -10000, fontSize: '0.875rem' }}>
      Loading your assessment history
    </Typography>
    {[0, 1, 2].map((i) => (
      <Box key={i} sx={{ py: 3.5, borderTop: 1, borderTopColor: 'divider' }}>
        <Skeleton variant="text" width={140} height={18} />
        <Skeleton variant="text" width="60%" height={26} sx={{ mt: 1 }} />
        <Skeleton variant="text" width="40%" height={20} sx={{ mt: 0.5 }} />
      </Box>
    ))}
  </Box>
);

export const HistoryPage: React.FC = () => {
  const { t } = useTranslations();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    offlineStorage
      .getAllSessions()
      .then((s) => setSessions(s as Session[]))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  const ordered = useMemo(
    () =>
      sessions
        .slice()
        .sort((a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime()),
    [sessions],
  );

  return (
    <Section>
      <SectionHeading
        as="h1"
        eyebrow="Your record"
        title={t('history.title')}
        lead="Assessments saved on this device, most recent first. Open any entry to review the guidance you were given."
        maxLead={600}
      />

      {loading ? (
        <HistorySkeleton />
      ) : ordered.length === 0 ? (
        /* ---------- Empty state: what is empty, why, and what to do ---------- */
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
            {t('history.empty')}
          </Typography>
          <Typography sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.secondary', mb: 3 }}>
            {t('history.emptyDesc')}
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
        /* ---------- Timeline ---------- */
        <Box component="ol" sx={{ listStyle: 'none', m: 0, p: 0, position: 'relative', maxWidth: 780 }}>
          {ordered.map((s, idx) => {
            const triage = lastTriage(s);
            const level = levelOf(s);
            const isLast = idx === ordered.length - 1;
            return (
              <Box
                component="li"
                key={s.session_id}
                sx={{ position: 'relative', display: 'flex', gap: { xs: 2.5, md: 4 } }}
              >
                {/* Rail + node */}
                <Box sx={{ position: 'relative', flexShrink: 0, width: 14, display: 'flex', justifyContent: 'center' }}>
                  <Box
                    aria-hidden="true"
                    sx={{
                      position: 'absolute',
                      top: 0,
                      bottom: isLast ? '50%' : 0,
                      width: 2,
                      backgroundColor: 'divider',
                    }}
                  />
                  <Box
                    aria-hidden="true"
                    sx={{
                      position: 'relative',
                      mt: 3,
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: colors.brand.primary,
                      border: '3px solid',
                      borderColor: 'background.default',
                      boxSizing: 'content-box',
                    }}
                  />
                </Box>

                {/* Entry */}
                <Box sx={{ flexGrow: 1, pb: isLast ? 0 : 5, pt: 2.5 }}>
                  <Typography component="p" sx={{ fontSize: '0.8125rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'text.secondary' }}>
                    {formatStamp(s.updated_at || s.created_at)}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mt: 1, mb: 1, flexWrap: 'wrap' }}>
                    <Typography component="h3" sx={{ fontSize: '1.125rem', fontWeight: 650, color: 'text.primary' }}>
                      {triage ? t('results.yourGuidance') : 'Assessment in progress'}
                    </Typography>
                    {triage && <SeverityBadge level={level} />}
                  </Box>

                  {triage?.suggested_next_step && (
                    <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary', maxWidth: 560, mb: 2 }}>
                      {triage.suggested_next_step}
                    </Typography>
                  )}

                  <Button
                    onClick={() => navigate(`/history/${s.session_id}`)}
                    size="small"
                    sx={{
                      px: 0,
                      color: colors.brand.primary,
                      fontWeight: 600,
                      textDecoration: 'underline',
                      textUnderlineOffset: 4,
                      '&:hover': { backgroundColor: 'transparent' },
                    }}
                  >
                    Open details
                  </Button>
                </Box>
              </Box>
            );
          })}
        </Box>
      )}

      {!loading && ordered.length > 0 && (
        <Typography sx={{ mt: 6, fontSize: '0.8125rem', lineHeight: 1.7, color: 'text.secondary', maxWidth: 620, opacity: 0.9 }}>
          This history is stored on this device only. Clearing your browser data or using another device will
          not show these entries.
        </Typography>
      )}
    </Section>
  );
};

export default HistoryPage;
