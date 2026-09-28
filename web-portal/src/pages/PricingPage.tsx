/**
 * DEDAN-Health — Pricing
 *
 * Master spec 15 / 44: this page must never misrepresent billing. Verified
 * facts about the current repository:
 *
 *   - The live v1 backend (`backend/main.py`) exposes NO billing routes.
 *   - `backend-v2/billing_endpoints.py` defines a router, but `main_v2.py`
 *     never `include_router`s it and the v2 app cannot import at all.
 *   - Therefore `billingService.isLive === false`.
 *
 * So: no prices, no currencies, no "most popular" badges, no checkout. We show
 * the intended global plan *structure* and state plainly that billing is not
 * live. The previous build rendered `billingService.isLive = false` as raw
 * developer text on the page — that debug output has been removed.
 */
import React from 'react';
import { Box, Typography, Button, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslations } from '../i18n';
import { Section, SectionHeading } from '../components/Section';
import { colors, radius } from '../design-system/tokens';

interface PlanShape {
  name: string;
  audience: string;
  includes: string[];
}

/** Intended structure only. Deliberately carries no price information. */
const PLANS: PlanShape[] = [
  {
    name: 'Patient',
    audience: 'Anyone seeking guidance for themselves or a family member',
    includes: [
      'Symptom assessment and urgency guidance',
      'Recommended next steps and escalation signs',
      'Assessment history on your device',
    ],
  },
  {
    name: 'Clinician',
    audience: 'Doctors, nurses and care teams reviewing AI-assisted assessments',
    includes: [
      'Everything in Patient',
      'Triage queue and priority review',
      'Clinical review and feedback on AI guidance',
    ],
  },
  {
    name: 'Organisation',
    audience: 'Clinics, hospitals and public health programmes',
    includes: [
      'Everything in Clinician',
      'Organisation-wide settings and audit trail',
      'Integration with existing clinical systems',
    ],
  },
];

export const PricingPage: React.FC = () => {
  const { t } = useTranslations();

  return (
    <Section>
      <SectionHeading
        as="h1"
        eyebrow={t('pricing.title')}
        title="Access is free while DEDAN is in preview."
        lead={t('pricing.desc')}
        maxLead={640}
      />

      {/* Honest status banner — not a marketing claim, a statement of fact. */}
      <Box
        sx={{
          p: { xs: 3, md: 4 },
          borderRadius: radius.xl,
          border: '1px solid rgba(46,125,50,0.20)',
          backgroundColor: 'rgba(46,125,50,0.05)',
          mb: { xs: 6, md: 8 },
          maxWidth: 780,
        }}
      >
        <Typography component="h2" sx={{ fontSize: '1.125rem', fontWeight: 700, color: 'text.primary', mb: 1 }}>
          Billing is not enabled yet
        </Typography>
        <Typography sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.secondary' }}>
          DEDAN does not process payments and no subscription can be purchased. There are no prices to show,
          and no plan below is currently purchasable. When billing ships, support for multiple currencies and
          regional payment providers is planned.
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
          gap: { xs: 4, md: 5 },
        }}
      >
        {PLANS.map((p) => (
          <Box
            key={p.name}
            sx={{
              borderTop: `2px solid ${colors.brand.primary}`,
              pt: 3,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Typography component="h3" sx={{ fontSize: '1.25rem', fontWeight: 700, color: 'text.primary' }}>
              {p.name}
            </Typography>
            <Typography sx={{ mt: 1, fontSize: '0.9375rem', lineHeight: 1.65, color: 'text.secondary' }}>
              {p.audience}
            </Typography>

            <Stack component="ul" spacing={1.25} sx={{ mt: 3, pl: 2.5, mb: 3, flexGrow: 1 }}>
              {p.includes.map((f) => (
                <Typography component="li" key={f} sx={{ fontSize: '0.9375rem', lineHeight: 1.65, color: 'text.secondary' }}>
                  {f}
                </Typography>
              ))}
            </Stack>

            <Button
              variant="outlined"
              disabled
              fullWidth
              sx={{ borderRadius: radius.pill, py: 1.25, borderColor: 'divider', color: 'text.secondary' }}
            >
              Not yet available
            </Button>
          </Box>
        ))}
      </Box>

      <Typography sx={{ mt: 6, fontSize: '0.875rem', lineHeight: 1.7, color: 'text.secondary', maxWidth: 640 }}>
        Basic symptom assessment will remain available without payment. Nothing on this page constitutes an
        offer, and no payment details are collected anywhere in this application.
      </Typography>

      <Box sx={{ mt: 5 }}>
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
    </Section>
  );
};

export default PricingPage;
