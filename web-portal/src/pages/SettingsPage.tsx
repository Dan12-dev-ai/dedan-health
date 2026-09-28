/**
 * DEDAN-Health — Settings
 *
 * Master spec 13: grouped categories, not a wall of cards. Every control here
 * performs a real action — the previous build shipped switches with
 * `onChange={() => {}}` (visual-only, i.e. deceptive UI). Those are gone.
 *
 * Live controls:
 *   - Appearance  -> DedanThemeProvider.setMode (persisted to localStorage)
 *   - Language    -> i18n.setLocale + DedanContext.setLanguage
 *   - Reduced motion -> reported from the OS (read-only; we cannot override an
 *     OS accessibility preference from a web app, so we state the truth).
 *   - Emergency contacts -> GET /dedan/v1/emergency-contacts (live v1 route)
 *   - Notifications -> no backend exists -> explicitly unavailable, not faked.
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Stack,
  Button,
  CircularProgress,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslations, getLocaleMeta, locales } from '../i18n';
import { useDedanTheme } from '../design-system/theme';
import { useDedanState } from '../state/DedanContext';
import { getEmergencyContacts } from '../services';
import { EmergencyContact, Language } from '../types';
import { Section, SectionHeading } from '../components/Section';
import { colors, radius } from '../design-system/tokens';

/** A grouped settings row: title + description + control on one baseline. */
const Row: React.FC<{
  title: string;
  description?: string;
  children?: React.ReactNode;
}> = ({ title, description, children }) => (
  <Box
    sx={{
      display: 'grid',
      gridTemplateColumns: { xs: '1fr', sm: '1fr auto' },
      gap: { xs: 2, sm: 4 },
      alignItems: 'start',
      py: 3,
      borderTop: 1,
      borderTopColor: 'divider',
    }}
  >
    <Box>
      <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
        {title}
      </Typography>
      {description && (
        <Typography sx={{ mt: 0.5, fontSize: '0.9375rem', lineHeight: 1.65, color: 'text.secondary', maxWidth: 520 }}>
          {description}
        </Typography>
      )}
    </Box>
    <Box sx={{ minWidth: { sm: 200 } }}>{children}</Box>
  </Box>
);

export const SettingsPage: React.FC = () => {
  const { t, setLocale, locale } = useTranslations();
  const { language, setLanguage } = useDedanState();
  const { userPreference, reducedMotion, setMode } = useDedanTheme();

  const [contacts, setContacts] = useState<EmergencyContact[] | null>(null);
  const [contactsError, setContactsError] = useState<string | null>(null);
  const [loadingContacts, setLoadingContacts] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingContacts(true);
    getEmergencyContacts()
      .then((res) => {
        if (cancelled) return;
        if (res.ok && Array.isArray(res.data)) {
          setContacts(
            (res.data as unknown[]).map((c, i) =>
              typeof c === 'string'
                ? { label: `Emergency line ${i + 1}`, number: c }
                : ({ ...(c as EmergencyContact) }),
            ),
          );
          setContactsError(null);
        } else if (!res.ok) {
          setContactsError(res.message);
        }
      })
      .catch(() => setContactsError('Could not reach the DEDAN service.'))
      .finally(() => !cancelled && setLoadingContacts(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const localeOptions = Object.keys(locales).map((code) => ({
    code,
    meta: getLocaleMeta(code),
  }));

  return (
    <Section>
      <SectionHeading
        as="h1"
        eyebrow="DEDAN Health"
        title="Settings"
        lead="Control how DEDAN looks, which language it uses, and what you share. Changes are saved on this device."
        maxLead={560}
      />

      {/* ---------------- Appearance ---------------- */}
      <Box component="section" aria-labelledby="settings-appearance">
        <Typography
          id="settings-appearance"
          component="h2"
          sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 2 }}
        >
          Appearance
        </Typography>

        <Row
          title="Theme"
          description="The default is the bright interface. Dark mode is available if you prefer lower contrast at night."
        >
          <ToggleButtonGroup
            value={userPreference}
            exclusive
            size="small"
            aria-label="Theme preference"
            onChange={(_e, v) => v && setMode(v)}
            sx={{
              '& .MuiToggleButton-root': {
                textTransform: 'none',
                borderRadius: radius.pill,
                px: 2.5,
                py: 1,
                borderColor: 'divider',
                '&.Mui-selected': {
                  backgroundColor: colors.brand.primary,
                  color: '#FFFFFF',
                  borderColor: colors.brand.primary,
                  '&:hover': { backgroundColor: colors.brand.primaryHover },
                },
              },
            }}
          >
            <ToggleButton value="light">Light</ToggleButton>
            <ToggleButton value="dark">Dark</ToggleButton>
            <ToggleButton value="system">System</ToggleButton>
          </ToggleButtonGroup>
        </Row>

        <Row
          title="Reduced motion"
          description={
            reducedMotion
              ? 'Your device requests reduced motion. DEDAN has disabled non-essential animation to respect this.'
              : 'Your device does not currently request reduced motion. This follows your operating system setting.'
          }
        >
          <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: reducedMotion ? 'success.main' : 'text.secondary' }}>
            {reducedMotion ? 'Enabled' : 'Not requested'}
          </Typography>
        </Row>
      </Box>

      {/* ---------------- Language ---------------- */}
      <Box component="section" aria-labelledby="settings-language" sx={{ mt: 8 }}>
        <Typography
          id="settings-language"
          component="h2"
          sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 2 }}
        >
          Language
        </Typography>

        <Row
          title="Interface language"
          description="Only languages with a complete translation are selectable. Clinical guidance language is handled by the assessment service."
        >
          <Select
            fullWidth
            size="small"
            value={locale}
            onChange={(e) => {
              const code = e.target.value;
              setLocale(code);
              setLanguage(code as Language);
            }}
            sx={{ borderRadius: radius.lg }}
            aria-label="Interface language"
          >
            {localeOptions.map(({ code, meta }) => (
              <MenuItem key={code} value={code} disabled={meta.status !== 'live'}>
                {meta.nativeLabel}
                {meta.status !== 'live' ? ' — translation unavailable' : ''}
              </MenuItem>
            ))}
          </Select>
        </Row>
      </Box>

      {/* ---------------- Privacy ---------------- */}
      <Box component="section" aria-labelledby="settings-privacy" sx={{ mt: 8 }}>
        <Typography
          id="settings-privacy"
          component="h2"
          sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 2 }}
        >
          Privacy & data
        </Typography>

        <Row
          title="Consent and data use"
          description="Review what DEDAN collects, why, and withdraw consent at any time."
        >
          <Button
            component={RouterLink}
            to="/consent"
            variant="outlined"
            sx={{ borderColor: 'divider', color: 'text.primary', borderRadius: radius.pill, px: 3 }}
          >
            {t('help.consent')}
          </Button>
        </Row>

        <Row
          title="Assessment history"
          description="Assessments are stored on this device. You can review or clear them from your history."
        >
          <Button
            component={RouterLink}
            to="/history"
            variant="outlined"
            sx={{ borderColor: 'divider', color: 'text.primary', borderRadius: radius.pill, px: 3 }}
          >
            {t('nav.history')}
          </Button>
        </Row>

        <Row
          title="Notifications"
          description="Reminders and follow-up notifications are not yet available. No notification will be sent until this is implemented."
        >
          <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: 'text.secondary' }}>
            Unavailable
          </Typography>
        </Row>
      </Box>

      {/* ---------------- Emergency contacts ---------------- */}
      <Box component="section" aria-labelledby="settings-emergency" sx={{ mt: 8 }}>
        <Typography
          id="settings-emergency"
          component="h2"
          sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 2 }}
        >
          Emergency contacts
        </Typography>

        <Box sx={{ borderTop: 1, borderTopColor: 'divider', pt: 3 }}>
          {loadingContacts && (
            <Stack direction="row" spacing={1.5} alignItems="center">
              <CircularProgress size={16} />
              <Typography sx={{ fontSize: '0.9375rem', color: 'text.secondary' }}>
                Loading emergency contacts…
              </Typography>
            </Stack>
          )}

          {!loadingContacts && contactsError && (
            <Typography sx={{ fontSize: '0.9375rem', color: 'text.secondary' }}>
              Emergency contacts could not be loaded from the service. This does not affect your ability to
              call your local emergency number.
            </Typography>
          )}

          {!loadingContacts && !contactsError && contacts && contacts.length === 0 && (
            <Typography sx={{ fontSize: '0.9375rem', color: 'text.secondary' }}>
              No emergency contacts are configured for your region.
            </Typography>
          )}

          {!loadingContacts && contacts && contacts.length > 0 && (
            <Stack spacing={1.5}>
              {contacts.map((c, i) => (
                <Box key={`${c.number}-${i}`} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 2, flexWrap: 'wrap' }}>
                  <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: 'text.primary' }}>
                    {c.label}
                  </Typography>
                  <Typography sx={{ fontSize: '1rem', color: 'text.secondary' }}>
                    {c.number}
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </Box>
      </Box>

      {/* ---------------- About ---------------- */}
      <Box component="section" aria-labelledby="settings-about" sx={{ mt: 8 }}>
        <Typography
          id="settings-about"
          component="h2"
          sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 2 }}
        >
          About DEDAN
        </Typography>

        <Box sx={{ borderTop: 1, borderTopColor: 'divider', pt: 3 }}>
          <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.75, color: 'text.secondary', maxWidth: 640 }}>
            DEDAN provides AI-assisted health guidance for informational and navigation purposes. It does not
            diagnose, treat, or replace professional medical care. Assessment guidance is generated from the
            information you provide and is labelled as AI-generated throughout.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mt: 3, flexWrap: 'wrap' }}>
            <Button component={RouterLink} to="/help" variant="outlined" sx={{ borderColor: 'divider', color: 'text.primary', borderRadius: radius.pill, px: 3 }}>
              {t('nav.help')}
            </Button>
            <Button component={RouterLink} to="/pricing" variant="outlined" sx={{ borderColor: 'divider', color: 'text.primary', borderRadius: radius.pill, px: 3 }}>
              {t('nav.pricing')}
            </Button>
          </Box>
        </Box>
      </Box>
    </Section>
  );
};

export default SettingsPage;
