/**
 * DEDAN-Health — Safety-critical UI components
 *
 * These are not presentational extras. `SeverityBadge` is how urgency reaches
 * the user, and its central invariant is that **colour is never the only
 * signal**: a user who cannot distinguish red from green, or who is using a
 * screen reader, must still receive the same information.
 *
 * That invariant is asserted here rather than assumed, because a regression
 * would be invisible in a snapshot and dangerous in production.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { SeverityBadge } from '../design-system/components/SeverityBadge';
import {
  AssessmentShell,
  ProgressIndicator,
} from '../components/assessment/AssessmentShell';
import type { TriageLevel } from '../types';

describe('SeverityBadge', () => {
  const cases: Array<[TriageLevel, string]> = [
    ['emergency', 'Emergency'],
    ['urgent', 'Urgent'],
    ['routine', 'Routine'],
    ['self_care', 'Self-care'],
  ];

  it.each(cases)('renders an accessible label for %s', (level, expected) => {
    render(<SeverityBadge level={level} />);
    // The accessible name must name the urgency, not just describe a chip.
    expect(screen.getByRole('status', { name: `Urgency level: ${expected}` })).toBeInTheDocument();
  });

  it('renders the level as visible text, so colour is not the only signal', () => {
    render(<SeverityBadge level="emergency" />);
    // If the label were icon-only, this text query would fail.
    expect(screen.getByText('Emergency')).toBeInTheDocument();
  });

  it('hides the text label only when explicitly asked, keeping the aria-label', () => {
    render(<SeverityBadge level="urgent" showLabel={false} />);
    expect(screen.queryByText('Urgent')).not.toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'Urgency level: Urgent' })).toBeInTheDocument();
  });

  it('distinguishes the most severe level from routine', () => {
    const { rerender } = render(<SeverityBadge level="emergency" />);
    const emergency = screen.getByRole('status').getAttribute('aria-label');
    rerender(<SeverityBadge level="routine" />);
    const routine = screen.getByRole('status').getAttribute('aria-label');
    expect(emergency).not.toBe(routine);
  });
});

describe('ProgressIndicator', () => {
  it('interpolates the step template and exposes progress to assistive tech', () => {
    render(<ProgressIndicator current={2} total={5} labelTemplate="Step {current} of {total}" />);
    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Step 2 of 5' })).toBeInTheDocument();
  });

  it('reports a mid-flow step as 40% complete', () => {
    render(<ProgressIndicator current={2} total={5} labelTemplate="Step {current} of {total}" />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '40');
  });
});

describe('AssessmentShell', () => {
  it('frames the question, lead text, and reassurance notice', () => {
    render(
      <AssessmentShell
        title="Describe your symptoms"
        lead="In your own words"
        notice="You can stop at any time."
      >
        <label htmlFor="symptom-input">Symptoms</label>
        <input id="symptom-input" />
      </AssessmentShell>,
    );

    expect(screen.getByRole('heading', { name: 'Describe your symptoms' })).toBeInTheDocument();
    expect(screen.getByText('In your own words')).toBeInTheDocument();
    expect(screen.getByText('You can stop at any time.')).toBeInTheDocument();
    expect(screen.getByLabelText('Symptoms')).toBeInTheDocument();
  });

  it('shows progress only when supplied', () => {
    const { rerender } = render(<AssessmentShell title="Step">content</AssessmentShell>);
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();

    rerender(
      <AssessmentShell
        title="Step"
        progress={{ current: 1, total: 3, labelTemplate: 'Step {current} of {total}' }}
      >
        content
      </AssessmentShell>,
    );
    expect(screen.getByRole('progressbar', { name: 'Step 1 of 3' })).toBeInTheDocument();
  });
});
