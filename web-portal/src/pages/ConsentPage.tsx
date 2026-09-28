/**
 * DEDAN-Health — Consent & data use
 *
 * Master spec 29: consent must be understandable, not a legal wall. Structure
 * answers the five questions a person actually has:
 *   What we collect -> Why -> How it is used -> Who can access it -> What you control
 *
 * The purpose list is submitted to the LIVE route
 * `POST /dedan/v1/session/{session_id}/consent`. Only purposes the backend
 * actually receives are selectable.
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Checkbox,
  FormControlLabel,
  Stack,
  Alert,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslations } from '../i18n';
import { useDedanState } from '../state/DedanContext';
import { saveConsent } from '../services';
import { Section, SectionHeading } from '../components/Section';
import { colors, radius } from '../design-system/tokens';

/** Purpose keys sent verbatim to the backend in `data_usage_purposes`. */
const PURPOSES = [
  {
    key: 'Provide your assessment',
    label: 'Provide your assessment and guidance',
    detail: 'Your information is used to generate the urgency level and next-step guidance you see.',
    required: true,
  },
  {
    key: 'Improve triage accuracy (anonymized)',
    label: 'Improve triage accuracy using anonymised data',
    detail: 'De-identified assessment data helps measure and improve the quality of guidance.',
    required: false,
  },
  {
    key: 'Send follow-up reminders you opt into',
    label: 'Send follow-up reminders',
    detail: 'Reminders are not implemented yet. Selecting this records your preference for when they ship.',
    required: false,
  },
];

/** The five consent questions, answered plainly. */
const EXPLAIN: { q: string; a: string }[] = [
  {
    q: 'What we collect',
    a: 'Your age, sex, optional location and long-term conditions, and the symptoms you describe. Nothing else is required to receive guidance.',
  },
  {
    q: 'Why we collect it',
    a: 'Each item changes how symptoms should be interpreted. Age, sex and pregnancy status in particular affect urgency for several symptom groups.',
  },
  {
    q: 'How it is used',
    a: 'Your information is sent to the DEDAN assessment service to produce your guidance. Purposes you do not select are never applied.',
  },
  {
    q: 'Who can access it',
    a: 'Your assessment history is stored on this device. Assessment requests are processed by the DEDAN service. DEDAN does not sell your information.',
  },
  {
    q: 'What you control',
    a: 'You choose which purposes apply, and you can withdraw consent at any time. Withdrawing consent stops the optional purposes immediately.',
  },
];

export const ConsentPage: React.FC = () => {
  const { t } = useTranslations();
  const { sessionId, profile } = useDedanState();

  const [purposes, setPurposes] = useState<Record<string, boolean>>({
    'Provide your assessment': true,
    'Improve triage accuracy (anonymized)': false,
    'Send follow-up reminders you opt into': false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);

  const toggle = (key: string) => setPurposes((p) => ({ ...p, [key]: !p[key] }));

  const handleSubmit = async () => {
    setSubmitting(true);
    setResult(null);
    const res = await saveConsent(sessionId, {
      consent_given: true,
      data_usage_purposes: Object.entries(purposes)
        .filter(([, v]) => v)
        .map(([k]) => k),
    });
    setSubmitting(false);
    setResult(
      res.ok
        ? { ok: true, msg: 'Your consent has been recorded.' }
        : {
            ok: false,
            msg:
              res.code === 'OFFLINE'
                ? 'You appear to be offline, so your consent could not be recorded. Nothing was lost — try again when you reconnect.'
                : `Your consent could not be recorded. ${res.message}`,
          },
    );
  };

  const noProfile = !profile;

  return (
    <Section>
      <SectionHeading
        as="h1"
        eyebrow={t('help.privacy')}
        title="Your data, and what happens to it"
        lead="DEDAN asks for the minimum information needed to give you useful guidance. This page explains exactly what that means."
        maxLead={640}
      />

      {/* ---------------- What / why / how / who / you ---------------- */}
      <Box sx={{ maxWidth: 820, mb: { xs: 8, md: 12 } }}>
        {EXPLAIN.map((e) => (
          <Box
            key={e.q}
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '220px 1fr' },
              gap: { xs: 1.5, md: 4 },
              py: 3.5,
              borderTop: 1,
              borderTopColor: 'divider',
            }}
          >
            <Typography component="h2" sx={{ fontSize: '1rem', fontWeight: 650, color: 'text.primary' }}>
              {e.q}
            </Typography>
            <Typography sx={{ fontSize: '1rem', lineHeight: 1.75, color: 'text.secondary' }}>
              {e.a}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* ---------------- Purpose-level consent ---------------- */}
      <Box sx={{ maxWidth: 720 }}>
        <Typography component="h2" sx={{ fontSize: { xs: '1.375rem', md: '1.625rem' }, fontWeight: 700, letterSpacing: '-0.02em', color: 'text.primary', mb: 1.5 }}>
          {t('help.consent')}
        </Typography>
        <Typography sx={{ fontSize: '1rem', lineHeight: 1.75, color: 'text.secondary', mb: 4 }}>
          Choose what DEDAN may use your information for. The first purpose is required to produce your
          assessment; the others are optional and off by default.
        </Typography>

        {noProfile && (
          <Alert severity="info" sx={{ mb: 4, borderRadius: radius.lg }}>
            You have not completed a patient profile yet. You can review this page now, and record your consent
            after your first assessment.
          </Alert>
        )}

        <Stack spacing={0}>
          {PURPOSES.map((p) => (
            <FormControlLabel
              key={p.key}
              sx={{
                alignItems: 'flex-start',
                m: 0,
                py: 3,
                borderTop: 1,
                borderTopColor: 'divider',
                '& .MuiCheckbox-root': { pt: 0.25 },
              }}
              control={
                <Checkbox
                  checked={Boolean(purposes[p.key])}
                  onChange={() => (p.required ? undefined : toggle(p.key))}
                  disabled={p.required}
                  inputProps={{ 'aria-describedby': `consent-${p.key}` }}
                />
              }
              label={
                <Box>
                  <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
                    {p.label}
                    {p.required && (
                      <Typography component="span" sx={{ ml: 1, fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: colors.brand.primary }}>
                        Required
                      </Typography>
                    )}
                  </Typography>
                  <Typography id={`consent-${p.key}`} sx={{ mt: 0.5, fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary', maxWidth: 560 }}>
                    {p.detail}
                  </Typography>
                </Box>
              }
            />
          ))}
        </Stack>

        <Box sx={{ mt: 5, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit}
            disabled={submitting}
            sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
          >
            {submitting ? 'Recording…' : 'Record my consent'}
          </Button>
          <Button
            component={RouterLink}
            to="/settings"
            variant="outlined"
            size="large"
            sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
          >
            {t('nav.settings')}
          </Button>
        </Box>

        {result && (
          <Alert severity={result.ok ? 'success' : 'error'} sx={{ mt: 4, borderRadius: radius.lg }} role="status">
            {result.msg}
          </Alert>
        )}
      </Box>
    </Section>
  );
};

export default ConsentPage;
