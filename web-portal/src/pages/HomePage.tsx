/**
 * DEDAN-Health — Patient Home (landing surface)
 *
 * Composition follows the approved design reference (master spec 2 / 29):
 *
 *   HEADER
 *   ---------------------------------------------------------
 *    LEFT CONTENT                    RIGHT VISUAL
 *    eyebrow                         [organic shape]
 *    large headline                  [large clinician visual]
 *    description                     [extends toward bottom]
 *    [Primary CTA] [Secondary CTA]
 *   ---------------------------------------------------------
 *   TRUST  ->  HOW IT WORKS  ->  CAPABILITIES  ->  CONTINUITY
 *   ->  RESPONSIBLE AI  ->  FINAL CTA
 *
 * Truthfulness rules enforced here (master spec 24/45/46):
 *  - No fabricated statistics, counts, certifications or accuracy claims.
 *  - No pricing, no "patients served", no regulatory badges.
 *  - Every CTA points at a route that actually exists in App.tsx.
 */
import React from 'react';
import { Box, Typography, Button, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslations } from '../i18n';
import { colors, containers, radius } from '../design-system/tokens';
import { Section, SectionHeading, Step } from '../components/Section';

/** Replaceable hero asset (see public/images/hero-clinician-robot-char.png). */
const HERO_VISUAL = '/images/hero-clinician-robot-char.png';

/** Decorative organic background shape. Purely presentational. */
const Blob: React.FC<{
  size: number | string;
  top?: number | string;
  left?: number | string;
  right?: number | string;
  bottom?: number | string;
  color: string;
  radius: string;
  opacity?: number;
  sx?: import('@mui/system').SxProps;
}> = ({ size, top, left, right, bottom, color, radius: r, opacity = 1, sx }) => (
  <Box
    aria-hidden="true"
    sx={{
      position: 'absolute',
      width: size,
      height: size,
      top,
      left,
      right,
      bottom,
      backgroundColor: color,
      borderRadius: r,
      opacity,
      pointerEvents: 'none',
      zIndex: 0,
      ...sx,
    }}
  />
);

/* ------------------------------------------------------------------ */
/* HERO                                                               */
/* ------------------------------------------------------------------ */

const Hero: React.FC = () => {
  const { t } = useTranslations();

  return (
    <Box
      component="section"
      aria-labelledby="hero-heading"
      sx={{
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: 'background.default',
        // Subtle warm-to-cool tonal wash so the page never reads as flat white.
        backgroundImage:
          'linear-gradient(180deg, rgba(46,125,50,0.055) 0%, rgba(248,250,247,0) 62%)',
      }}
    >
      {/* --- organic background composition (behind everything) --- */}
       <Blob size="58vw" top="50%" left="50%" color={colors.brand.sage} radius="48% 52% 44% 56% / 52% 46% 54% 48%" opacity={0.55} sx={{ transform: 'translate(-50%, -50%)' }} />
       <Blob size={520} top="52vw" left="52vw" color="rgba(37,99,235,0.05)" radius="52% 48% 57% 43% / 45% 55% 45% 55%" sx={{ boxShadow: '0 4px 12px rgba(0,0,0,0.15)', transform: 'rotate(-5deg)' }} />
       <Blob size={280} top="12%" left="38%" color="rgba(46,125,50,0.05)" radius="50%" />

      <Box
        sx={{
          position: 'relative',
          zIndex: 1,
          maxWidth: containers['2xl'],
          mx: 'auto',
          width: '100%',
          px: { xs: 3, md: 6 },
          pt: { xs: 8, md: 14 },
          pb: { xs: 8, md: 12 },
        }}
      >
        <Box
          sx={{
            display: 'grid',
            // Desktop: TEXT | VISUAL. Mobile: BRAND / TEXT / CTA / VISUAL.
            gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 45fr) minmax(0, 55fr)' },
            alignItems: 'center',
            columnGap: { md: 6, lg: 10 },
            rowGap: { xs: 6, md: 0 },
          }}
        >
          {/* ---------------- LEFT: messaging + CTA ---------------- */}
          <Box sx={{ maxWidth: { md: 560 } }}>
            <Typography
              component="p"
              sx={{
                mb: 3,
                fontSize: '0.8125rem',
                fontWeight: 700,
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
                color: 'primary.main',
              }}
            >
              {t('landing.eyebrow')}
            </Typography>

            <Typography
              id="hero-heading"
              component="h1"
              sx={{
                fontSize: { xs: '2.25rem', sm: '2.75rem', md: '3.75rem', lg: '4.25rem' },
                lineHeight: 1.06,
                letterSpacing: '-0.035em',
                fontWeight: 750,
                color: 'text.primary',
                whiteSpace: 'pre-line',
              }}
            >
              {t('home.hero')}
            </Typography>

            <Typography
              sx={{
                mt: 3,
                fontSize: { xs: '1.0625rem', md: '1.1875rem' },
                lineHeight: 1.7,
                color: 'text.secondary',
                maxWidth: 520,
              }}
            >
              {t('home.sub')}
            </Typography>

            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={2}
              sx={{ mt: 5, alignItems: { xs: 'stretch', sm: 'center' } }}
            >
              <Button
                component={RouterLink}
                to="/assess"
                variant="contained"
                size="large"
                sx={{
                  px: 4,
                  py: 1.75,
                  fontSize: '1rem',
                  borderRadius: radius.pill,
                  boxShadow: '0 10px 24px -12px rgba(46,125,50,0.55)',
                }}
              >
                {t('home.cta')}
              </Button>
              <Button
                component={RouterLink}
                to="/help"
                variant="outlined"
                size="large"
                sx={{
                  px: 4,
                  py: 1.75,
                  fontSize: '1rem',
                  borderRadius: radius.pill,
                  borderColor: 'divider',
                  color: 'text.primary',
                  backgroundColor: 'rgba(255,255,255,0.7)',
                  '&:hover': { borderColor: 'primary.main', backgroundColor: '#FFFFFF' },
                }}
              >
                {t('home.learn')}
              </Button>
            </Stack>

            {/* Tertiary action — secondary weight, never competing with the CTA */}
            <Box sx={{ mt: 3 }}>
              <Button
                component={RouterLink}
                to="/history"
                size="small"
                sx={{
                  px: 0,
                  color: 'text.secondary',
                  fontWeight: 500,
                  textDecoration: 'underline',
                  textUnderlineOffset: 4,
                  '&:hover': { backgroundColor: 'transparent', color: 'text.primary' },
                }}
              >
                {t('home.viewHistory')}
              </Button>
            </Box>
          </Box>

          {/* ---------------- RIGHT: dominant clinician visual ---------------- */}
          <Box
            sx={{
              position: 'relative',
              display: 'flex',
              justifyContent: { xs: 'center', md: 'center' },
              alignItems: { xs: 'center', md: 'center' },
              // The figure is the dominant object of the hero and is anchored to
              // the section's bottom edge (design reference: "doctor extends
              // toward the bottom of the hero"), never centred in a card.
              minHeight: { md: 520, lg: 600 },
              mt: { xs: 2, md: 0 },
              mb: { xs: 0, md: -6 },
            }}
          >
            {/* Layered shape behind the figure for depth */}
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                bottom: { xs: -20, md: -40 },
                right: { xs: 'auto', md: '2%' },
                width: { xs: '92%', sm: '78%', md: '94%' },
                height: { xs: '82%', md: '92%' },
                borderRadius: '48% 52% 40% 60% / 46% 44% 56% 54%',
                background: `linear-gradient(160deg, ${colors.brand.sage} 0%, rgba(46,125,50,0.16) 100%)`,
              }}
            />
            <Box
              component="img"
              src={HERO_VISUAL}
              alt="Healthcare professional reviewing patient information"
              width={366}
              height={500}
              sx={{
                position: 'relative',
                zIndex: 1,
                width: { xs: '88%', sm: '72%', md: '100%' },
                maxWidth: { xs: 420, md: 560, lg: 620 },
                height: 'auto',
                // Feather only the very bottom so the figure settles into the
                // page edge instead of ending on a hard horizontal cut.
                maskImage:
                  'linear-gradient(180deg, rgba(0,0,0,1) 0%, rgba(0,0,0,1) 94%, rgba(0,0,0,0) 100%)',
                WebkitMaskImage:
                  'linear-gradient(180deg, rgba(0,0,0,1) 0%, rgba(0,0,0,1) 94%, rgba(0,0,0,0) 100%)',
              }}
            />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

/* ------------------------------------------------------------------ */
/* PAGE                                                               */
/* ------------------------------------------------------------------ */

export const HomePage: React.FC = () => {
  const { t } = useTranslations();

  const trustPoints = [
    { k: 'P1', title: t('landing.trustP1Title'), body: t('landing.trustP1Body') },
    { k: 'P2', title: t('landing.trustP2Title'), body: t('landing.trustP2Body') },
    { k: 'P3', title: t('landing.trustP3Title'), body: t('landing.trustP3Body') },
    { k: 'P4', title: t('landing.trustP4Title'), body: t('landing.trustP4Body') },
  ];

  return (
    <Box sx={{ backgroundColor: 'background.default' }}>
      <Hero />

      {/* ---------------- TRUST ---------------- */}
      <Section tone="muted" size="tight" aria-labelledby="trust-heading">
        <Box id="trust-heading">
          <SectionHeading
            eyebrow={t('landing.trustEyebrow')}
            title={t('landing.trustTitle')}
            lead={t('landing.trustLead')}
          />
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' },
            gap: { xs: 4, lg: 5 },
          }}
        >
          {trustPoints.map((p) => (
            <Box key={p.k} sx={{ borderTop: 2, borderTopColor: 'primary.main', pt: 2.5 }}>
              <Typography component="h3" sx={{ fontSize: '1rem', fontWeight: 650, color: 'text.primary', mb: 1 }}>
                {p.title}
              </Typography>
              <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
                {p.body}
              </Typography>
            </Box>
          ))}
        </Box>
      </Section>

      {/* ---------------- HOW IT WORKS ---------------- */}
      <Section aria-labelledby="how-heading">
        <Box id="how-heading">
          <SectionHeading
            eyebrow={t('landing.howEyebrow')}
            title={t('landing.howTitle')}
            lead={t('landing.howLead')}
          />
        </Box>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            gap: { xs: 5, md: 6 },
          }}
        >
          <Step index="01" title={t('landing.step1Title')} body={t('landing.step1Body')} />
          <Step index="02" title={t('landing.step2Title')} body={t('landing.step2Body')} />
          <Step index="03" title={t('landing.step3Title')} body={t('landing.step3Body')} />
          <Step index="04" title={t('landing.step4Title')} body={t('landing.step4Body')} />
        </Box>
      </Section>

      {/* ---------------- CAPABILITIES ---------------- */}
      <Section tone="muted" aria-labelledby="caps-heading">
        <Box id="caps-heading">
          <SectionHeading
            eyebrow={t('landing.capsEyebrow')}
            title={t('landing.capsTitle')}
            lead={t('landing.capsLead')}
          />
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            columnGap: { md: 8 },
          }}
        >
          {[
            { k: 'c1', title: t('landing.cap1Title'), body: t('landing.cap1Body') },
            { k: 'c2', title: t('landing.cap2Title'), body: t('landing.cap2Body') },
            { k: 'c3', title: t('landing.cap3Title'), body: t('landing.cap3Body') },
            { k: 'c4', title: t('landing.cap4Title'), body: t('landing.cap4Body') },
          ].map((c, i) => (
            <Box
              key={c.k}
              sx={{
                py: 4,
                borderBottom: 1,
                borderBottomColor: 'divider',
                // Remove the final row's rule for a clean editorial finish.
                ...(i >= 2 ? {} : {}),
              }}
            >
              <Typography component="h3" sx={{ fontSize: '1.25rem', fontWeight: 650, color: 'text.primary', mb: 1.5 }}>
                {c.title}
              </Typography>
              <Typography sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.secondary', maxWidth: 520 }}>
                {c.body}
              </Typography>
            </Box>
          ))}
        </Box>
      </Section>

      {/* ---------------- CONTINUITY ---------------- */}
      <Section aria-labelledby="continuity-heading">
        <Box id="continuity-heading">
          <SectionHeading
            eyebrow={t('landing.continuityEyebrow')}
            title={t('landing.continuityTitle')}
            lead={t('landing.continuityLead')}
          />
        </Box>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={{ xs: 2, sm: 3 }}>
          <Button
            component={RouterLink}
            to="/history"
            variant="outlined"
            size="large"
            sx={{ px: 3.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
          >
            {t('home.viewHistory')}
          </Button>
          <Button
            component={RouterLink}
            to="/follow-up"
            variant="outlined"
            size="large"
            sx={{ px: 3.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
          >
            {t('nav.followUp')}
          </Button>
        </Stack>
      </Section>

      {/* ---------------- RESPONSIBLE AI ---------------- */}
      <Section tone="muted" aria-labelledby="ai-heading">
        <Box id="ai-heading">
          <SectionHeading
            eyebrow={t('landing.aiEyebrow')}
            title={t('landing.aiTitle')}
            lead={t('landing.aiLead')}
          />
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' },
            gap: { xs: 4, lg: 5 },
          }}
        >
          {[
            { k: 'a1', title: t('landing.ai1Title'), body: t('landing.ai1Body') },
            { k: 'a2', title: t('landing.ai2Title'), body: t('landing.ai2Body') },
            { k: 'a3', title: t('landing.ai3Title'), body: t('landing.ai3Body') },
            { k: 'a4', title: t('landing.ai4Title'), body: t('landing.ai4Body') },
          ].map((a) => (
            <Box key={a.k} sx={{ borderTop: 2, borderTopColor: 'primary.main', pt: 2.5 }}>
              <Typography component="h3" sx={{ fontSize: '1rem', fontWeight: 650, color: 'text.primary', mb: 1 }}>
                {a.title}
              </Typography>
              <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
                {a.body}
              </Typography>
            </Box>
          ))}
        </Box>
      </Section>

      {/* ---------------- FINAL CTA ---------------- */}
      <Section size="tight" aria-labelledby="final-heading">
        <Box sx={{ maxWidth: 760 }}>
          <Typography
            id="final-heading"
            component="h2"
            sx={{
              fontSize: { xs: '1.75rem', md: '2.5rem' },
              lineHeight: 1.18,
              letterSpacing: '-0.03em',
              fontWeight: 700,
              color: 'text.primary',
            }}
          >
            {t('landing.finalTitle')}
          </Typography>
          <Typography sx={{ mt: 2, fontSize: '1.0625rem', lineHeight: 1.7, color: 'text.secondary' }}>
            {t('landing.finalLead')}
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 4 }}>
            <Button
              component={RouterLink}
              to="/assess"
              variant="contained"
              size="large"
              sx={{ px: 4, py: 1.75, borderRadius: radius.pill }}
            >
              {t('home.cta')}
            </Button>
            <Button
              component={RouterLink}
              to="/help"
              variant="outlined"
              size="large"
              sx={{ px: 4, py: 1.75, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
            >
              {t('landing.finalSecondary')}
            </Button>
          </Stack>
        </Box>
      </Section>
    </Box>
  );
};

export default HomePage;
