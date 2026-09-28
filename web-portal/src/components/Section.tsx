import React from 'react';
import { Box, Typography } from '@mui/material';
import { containers, radius } from '../design-system/tokens';

/**
 * Shared page primitives.
 *
 * `Section` gives every band on a page the SAME horizontal rhythm and vertical
 * breathing room (master spec 19/48: real spacing scale, not a grid of cards).
 * `SectionHeading` encodes the eyebrow -> title -> lead hierarchy once.
 */

export interface SectionProps {
  children: React.ReactNode;
  /** Background treatment. `plain` = page background, `muted` = tonal surface. */
  tone?: 'plain' | 'muted';
  /** Vertical rhythm. `normal` = 96/128px, `tight` = 64/80px. */
  size?: 'tight' | 'normal';
  id?: string;
  'aria-labelledby'?: string;
}

export const Section: React.FC<SectionProps> = ({
  children,
  tone = 'plain',
  size = 'normal',
  id,
  ...rest
}) => (
  <Box
    id={id}
    component="section"
    {...rest}
    sx={{
      width: '100%',
      backgroundColor: tone === 'muted' ? 'rgba(46, 125, 50, 0.045)' : 'transparent',
    }}
  >
    <Box
      sx={{
        maxWidth: containers['2xl'],
        mx: 'auto',
        width: '100%',
        px: { xs: 3, md: 6 },
        py: size === 'tight' ? { xs: 6, md: 10 } : { xs: 8, md: 16 },
      }}
    >
      {children}
    </Box>
  </Box>
);

export interface SectionHeadingProps {
  eyebrow?: string;
  title: React.ReactNode;
  lead?: React.ReactNode;
  align?: 'start' | 'center';
  /** Constrain the lead width so long copy never runs the full page width. */
  maxLead?: number;
  /**
   * Semantic heading level. Use `h1` when this heading IS the page title, and
   * the default `h2` when it heads a section inside a page. Exactly one `h1`
   * must exist per page (WCAG 1.3.1 / logical heading order).
   */
  as?: 'h1' | 'h2';
}

export const SectionHeading: React.FC<SectionHeadingProps> = ({
  eyebrow,
  title,
  lead,
  align = 'start',
  maxLead = 640,
  as: Heading = 'h2',
}) => (
  <Box sx={{ mb: { xs: 5, md: 8 }, textAlign: align === 'center' ? 'center' : 'start' }}>
    {eyebrow && (
      <Typography
        component="p"
        sx={{
          mb: 1.5,
          fontSize: '0.8125rem',
          fontWeight: 700,
          letterSpacing: '0.14em',
          textTransform: 'uppercase',
          color: 'primary.main',
        }}
      >
        {eyebrow}
      </Typography>
    )}
    <Typography
      component={Heading}
      sx={{
        fontSize: { xs: '1.75rem', md: '2.5rem' },
        lineHeight: 1.18,
        letterSpacing: '-0.025em',
        fontWeight: 700,
        color: 'text.primary',
        maxWidth: align === 'center' ? 900 : 820,
        mx: align === 'center' ? 'auto' : 0,
      }}
    >
      {title}
    </Typography>
    {lead && (
      <Typography
        sx={{
          mt: 2.5,
          fontSize: { xs: '1.0625rem', md: '1.1875rem' },
          lineHeight: 1.65,
          color: 'text.secondary',
          maxWidth: maxLead,
          mx: align === 'center' ? 'auto' : 0,
        }}
      >
        {lead}
      </Typography>
    )}
  </Box>
);

export interface StepProps {
  index: string;
  title: string;
  body: string;
}

/** Numbered editorial step (master spec 7) — NOT a card. */
export const Step: React.FC<StepProps> = ({ index, title, body }) => (
  <Box sx={{ flex: 1, minWidth: 220 }}>
    <Typography
      component="span"
      sx={{
        display: 'block',
        fontSize: '2.25rem',
        fontWeight: 700,
        letterSpacing: '-0.035em',
        color: 'primary.main',
        opacity: 0.28,
        lineHeight: 1,
        mb: 2,
      }}
    >
      {index}
    </Typography>
    <Typography
      component="h3"
      sx={{ fontSize: '1.125rem', fontWeight: 650, color: 'text.primary', mb: 1 }}
    >
      {title}
    </Typography>
    <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
      {body}
    </Typography>
  </Box>
);

export default Section;
