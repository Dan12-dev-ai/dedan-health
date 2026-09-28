import React from 'react';
import { Chip, ChipProps, SvgIconProps } from '@mui/material';
import { TriageLevel } from '../../types';
import { colors, radius } from '../tokens';
import {
  ErrorOutlineIcon,
  WarningIcon,
  InfoOutlineIcon,
  CheckCircleIcon,
} from './icons';

/**
 * Severity badge.
 *
 * Master spec 6 / 22: colour is NEVER the only signal. The badge always renders
 * a word (`Emergency` / `Urgent` / `Routine` / `Self-care`) alongside a
 * distinct icon, and carries an explicit `aria-label` for screen readers.
 *
 * The icon comes from the single design-system icon set (master spec 34) rather
 * than ad-hoc emoji, so stroke weight and optical size stay consistent with the
 * rest of the interface.
 */
type SeverityMeta = {
  label: string;
  bg: string;
  fg: string;
  Icon: React.ComponentType<SvgIconProps>;
};

const severityMeta: Record<TriageLevel, SeverityMeta> = {
  emergency: { label: 'Emergency', bg: colors.critical.base, fg: colors.critical.contrast, Icon: ErrorOutlineIcon },
  urgent: { label: 'Urgent', bg: colors.warning.base, fg: colors.warning.contrast, Icon: WarningIcon },
  routine: { label: 'Routine', bg: colors.info.base, fg: colors.info.contrast, Icon: InfoOutlineIcon },
  self_care: { label: 'Self-care', bg: colors.success.base, fg: colors.success.contrast, Icon: CheckCircleIcon },
};

export interface SeverityBadgeProps extends Omit<ChipProps, 'children' | 'onClick' | 'icon'> {
  level: TriageLevel;
  /** Never rely on colour alone — the label is rendered by default. */
  showLabel?: boolean;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  level,
  showLabel = true,
  sx,
  ...rest
}) => {
  const meta = severityMeta[level];
  const { Icon } = meta;

  return (
    <Chip
      role="status"
      aria-label={`Urgency level: ${meta.label}`}
      label={
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, lineHeight: 1.2 }}>
          <Icon sx={{ fontSize: '1rem', color: 'inherit' }} />
          {showLabel ? meta.label : null}
        </span>
      }
      clickable={false}
      sx={{
        backgroundColor: meta.bg,
        color: meta.fg,
        fontWeight: 650,
        fontSize: '0.8125rem',
        height: 'auto',
        minHeight: '1.75rem',
        borderRadius: radius.pill,
        px: showLabel ? 1.5 : 1,
        '& .MuiChip-label': {
          padding: 0,
          display: 'inline-flex',
          alignItems: 'center',
        },
        ...sx,
      }}
      {...rest}
    />
  );
};

export default SeverityBadge;
