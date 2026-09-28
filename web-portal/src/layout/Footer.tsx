import React from 'react';
import { Box, Typography } from '@mui/material';
import { NavLink } from 'react-router-dom';
import { Logo } from '../design-system/components';
import { containers } from '../design-system/tokens';

/**
 * Patient footer.
 *
 * Secondary destinations (master spec 52) live here rather than in the header,
 * keeping the top navigation lightweight. Only routes that actually exist in
 * `App.tsx` are linked — no dead links (master spec 60).
 */
const secondary = [
  { to: '/history', label: 'Assessment history' },
  { to: '/follow-up', label: 'Follow-up' },
  { to: '/settings', label: 'Settings' },
  { to: '/consent', label: 'Consent & data use' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/help', label: 'Help centre' },
] as const;

const linkSx = {
  display: 'block',
  py: 0.75,
  textDecoration: 'none',
  color: 'text.secondary',
  fontSize: '0.9375rem',
  transition: 'color 140ms ease',
  '&:hover': { color: 'text.primary' },
} as const;

export const Footer: React.FC = () => (
  <Box
    component="footer"
    sx={{
      width: '100%',
      borderTop: 1,
      borderTopColor: 'divider',
      backgroundColor: 'rgba(46, 125, 50, 0.035)',
    }}
  >
    <Box
      sx={{
        maxWidth: containers['2xl'],
        mx: 'auto',
        width: '100%',
        px: { xs: 3, md: 6 },
        py: { xs: 6, md: 8 },
      }}
    >
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '2fr 1fr 1fr' },
          gap: { xs: 5, md: 8 },
        }}
      >
        {/* Brand + responsibility statement */}
        <Box sx={{ maxWidth: 420 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
            <Logo sx={{ fontSize: 26 }} />
            <Typography sx={{ fontWeight: 700, letterSpacing: '-0.02em', color: 'text.primary' }}>
              DEDAN&nbsp;Health
            </Typography>
          </Box>
          <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
            AI-assisted health guidance for informational and navigation purposes. DEDAN does not
            diagnose, treat, or replace professional medical care. In an emergency, contact your
            local emergency number immediately.
          </Typography>
        </Box>

        <Box component="nav" aria-label="Patient links">
          <Typography
            component="h2"
            sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.primary', mb: 1.5 }}
          >
            Your health
          </Typography>
          {secondary.slice(0, 3).map((l) => (
            <Box key={l.to} component={NavLink} to={l.to} sx={linkSx}>
              {l.label}
            </Box>
          ))}
        </Box>

        <Box component="nav" aria-label="Support and legal links">
          <Typography
            component="h2"
            sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.primary', mb: 1.5 }}
          >
            Trust & support
          </Typography>
          {secondary.slice(3).map((l) => (
            <Box key={l.to} component={NavLink} to={l.to} sx={linkSx}>
              {l.label}
            </Box>
          ))}
        </Box>
      </Box>

      <Typography
        sx={{
          mt: { xs: 6, md: 8 },
          pt: 4,
          borderTop: 1,
          borderTopColor: 'divider',
          fontSize: '0.8125rem',
          color: 'text.secondary',
        }}
      >
        &copy; {new Date().getFullYear()} DEDAN Health. Clinical guidance references are shown in each
        assessment. This interface is a demonstration build; deployment, regulatory status and
        jurisdiction-specific compliance are not asserted here.
      </Typography>
    </Box>
  </Box>
);

export default Footer;
