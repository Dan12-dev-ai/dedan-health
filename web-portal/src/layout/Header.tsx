import React from 'react';
import { Box, Toolbar, Typography, Button, Divider } from '@mui/material';
import { NavLink } from 'react-router-dom';
import { Logo } from '../design-system/components';
import { useTranslations } from '../i18n';
import { colors, spacing, radius } from '../design-system/tokens';

/**
 * Primary patient navigation (master spec 52 / 20).
 * Lightweight, horizontal, premium — NOT a dashboard navbar.
 * Secondary destinations (Profile, Settings, Consent, Pricing) live in the
 * footer to keep the header uncluttered. Updated.
 */
const navLinks = [
  { to: '/', labelKey: 'nav.home' },
  { to: '/assess', labelKey: 'nav.assess' },
  { to: '/history', labelKey: 'nav.history' },
  { to: '/follow-up', labelKey: 'nav.followUp' },
  { to: '/help', labelKey: 'nav.help' },
] as const;

export const Header: React.FC = () => {
  const { t } = useTranslations();

  return (
    <Box
      component="header"
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 1200,
        bgcolor: 'background.default',
        borderBottom: 1,
        borderBottomColor: 'divider',
      }}
    >
      <Toolbar
        disableGutters
        sx={{
          width: '100%',
          px: { xs: 3, md: 5 },
          minHeight: { xs: 90, md: 110 },
          gap: 4,
          alignItems: 'center',
        }}
      >
        {/* Brand — Large logo matching image aspect ratio (1408x768 ≈ 1.83:1) */}
        <Box
          component={NavLink}
          to="/"
          aria-label="DEDAN Health — home"
          sx={{
            display: 'flex',
            alignItems: 'center',
            textDecoration: 'none',
            color: 'text.primary',
            flexShrink: 0,
            minWidth: 0,
          }}
        >
          <Logo
            width={180}
            height={100}
          />
        </Box>

        {/* Primary navigation */}
        <Box
          component="nav"
          aria-label="Primary navigation"
          sx={{
            display: { xs: 'none', md: 'flex' },
            alignItems: 'center',
            gap: 4,
            ml: 'auto',
          }}
        >
          {navLinks.map((l) => (
            <Box
              key={l.to}
              component={NavLink}
              to={l.to}
              end={l.to === '/'}
              sx={{
                position: 'relative',
                textDecoration: 'none',
                color: 'text.secondary',
                fontSize: '0.9375rem',
                fontWeight: 500,
                py: 0.5,
                transition: 'color 140ms ease',
                '&:hover': { color: 'text.primary' },
                '&.active': {
                  color: 'text.primary',
                  fontWeight: 600,
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    left: 0,
                    right: 0,
                    bottom: -2,
                    height: 2,
                    borderRadius: radius.pill,
                    backgroundColor: colors.brand.primary,
                  },
                },
              }}
            >
              {t(l.labelKey)}
            </Box>
          ))}
        </Box>

        {/* Primary action — only offered when not already assessing */}
        <Box sx={{ ml: { xs: 'auto', md: 0 }, flexShrink: 0 }}>
          <Button
            component={NavLink}
            to="/assess"
            variant="contained"
            size="large"
            sx={{ px: { xs: 2.5, md: 3.5 }, borderRadius: radius.pill }}
          >
            {t('home.cta')}
          </Button>
        </Box>
      </Toolbar>
    </Box>
  );
};

export default Header;

