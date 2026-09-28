import React from 'react';
import { Box, Typography, Button, LinearProgress } from '@mui/material';
import { containers, radius } from '../../design-system/tokens';

/**
 * Guided assessment shell (master spec 8).
 *
 * Gives the assessment a calm, single-purpose frame:
 *   progress  ->  question  ->  supporting explanation  ->  input  ->  back/continue
 *
 * Deliberately NOT a chat transcript and NOT a bare form: one question group is
 * in focus at a time, and the primary action is always in the same place.
 *
 * Navigation is rendered with `type="button"`/`submit` separately so the caller
 * controls form semantics (progressive disclosure over one big form).
 */

export interface ProgressIndicatorProps {
  /** 1-based index of the current step. */
  current: number;
  total: number;
  /** Localised template, e.g. "Step {current} of {total}". */
  labelTemplate: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  current,
  total,
  labelTemplate,
}) => {
  const pct = Math.round((current / total) * 100);
  const label = labelTemplate
    .replace('{current}', String(current))
    .replace('{total}', String(total));

  return (
    <Box sx={{ mb: 4 }}>
      <Typography
        component="p"
        sx={{
          mb: 1,
          fontSize: '0.8125rem',
          fontWeight: 700,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'text.secondary',
        }}
      >
        {label}
      </Typography>
      <LinearProgress
        variant="determinate"
        value={pct}
        aria-label={label}
        sx={{
          height: 6,
          borderRadius: radius.pill,
          backgroundColor: 'rgba(46,125,50,0.12)',
          '& .MuiLinearProgress-bar': { borderRadius: radius.pill },
        }}
      />
    </Box>
  );
};

export interface AssessmentShellProps {
  /** Main content. Optional so the shell can also frame an empty/error state. */
  children?: React.ReactNode;
  title: string;
  lead?: string;
  progress?: ProgressIndicatorProps;
  /** Footer actions (Back / Continue). Rendered in a stable, sticky-ish row. */
  actions?: React.ReactNode;
  /** Optional short reassurance note above the actions. */
  notice?: string;
}

export const AssessmentShell: React.FC<AssessmentShellProps> = ({
  children,
  title,
  lead,
  progress,
  actions,
  notice,
}) => (
  <Box
    component="section"
    aria-labelledby="assessment-heading"
    sx={{
      width: '100%',
      backgroundColor: 'background.default',
      backgroundImage:
        'linear-gradient(180deg, rgba(46,125,50,0.05) 0%, rgba(248,250,247,0) 55%)',
      pb: { xs: 8, md: 12 },
    }}
  >
    <Box
      sx={{
        maxWidth: 960,
        mx: 'auto',
        width: '100%',
        px: { xs: 3, md: 4 },
        pt: { xs: 6, md: 10 },
      }}
    >
      {progress && (
        <ProgressIndicator
          current={progress.current}
          total={progress.total}
          labelTemplate={progress.labelTemplate}
        />
      )}

      <Typography
        id="assessment-heading"
        component="h1"
        sx={{
          fontSize: { xs: '1.75rem', md: '2.5rem' },
          lineHeight: 1.15,
          letterSpacing: '-0.03em',
          fontWeight: 700,
          color: 'text.primary',
        }}
      >
        {title}
      </Typography>

      {lead && (
        <Typography
          sx={{
            mt: 2,
            fontSize: { xs: '1rem', md: '1.125rem' },
            lineHeight: 1.7,
            color: 'text.secondary',
            maxWidth: 620,
          }}
        >
          {lead}
        </Typography>
      )}

      <Box sx={{ mt: { xs: 5, md: 7 } }}>{children}</Box>

      {notice && (
        <Box
          sx={{
            mt: 5,
            p: 2.5,
            borderRadius: radius.lg,
            backgroundColor: 'rgba(46,125,50,0.06)',
            border: '1px solid rgba(46,125,50,0.16)',
          }}
        >
          <Typography sx={{ fontSize: '0.9375rem', color: 'text.secondary' }}>
            {notice}
          </Typography>
        </Box>
      )}

      {actions && (
        <Box
          sx={{
            mt: { xs: 6, md: 8 },
            pt: 4,
            borderTop: 1,
            borderTopColor: 'divider',
            display: 'flex',
            gap: 2,
            flexDirection: { xs: 'column-reverse', sm: 'row' },
            alignItems: { xs: 'stretch', sm: 'center' },
          }}
        >
          {actions}
        </Box>
      )}
    </Box>
  </Box>
);

export default AssessmentShell;
