/**
 * DEDAN-Health — Help & education
 *
 * Master spec 12: an editorial help surface, not a bare accordion page. The
 * FAQ accordion is retained but demoted to the end — the primary content is
 * readable, structured explanation.
 *
 * All content here is descriptive of the ACTUAL system. Urgency levels listed
 * are exactly the four the backend returns (`backend/models.py::TriageLevel`).
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Link as RouterLink } from 'react-router-dom';
import { Button } from '@mui/material';
import { SeverityBadge } from '../design-system/components';
import { Section, SectionHeading } from '../components/Section';
import { TriageLevel } from '../types';
import { colors, radius } from '../design-system/tokens';

/** Explanation of each urgency level, keyed to the real TriageLevel enum. */
const LEVELS: { level: TriageLevel; body: string; action: string }[] = [
  {
    level: 'emergency',
    body: 'Your responses indicate a possible life-threatening situation.',
    action: 'Contact emergency services or go to the nearest emergency department immediately.',
  },
  {
    level: 'urgent',
    body: 'Your responses suggest you should be assessed by a clinician soon.',
    action: 'Seek medical evaluation today — contact a clinic or urgent care service.',
  },
  {
    level: 'routine',
    body: 'Your responses do not indicate an immediate emergency, but you should follow up.',
    action: 'Arrange an appointment with a healthcare professional and monitor your symptoms.',
  },
  {
    level: 'self_care',
    body: 'Your responses suggest the symptoms can reasonably be managed while you monitor them.',
    action: 'Manage your symptoms, monitor for change, and seek care if things worsen.',
  },
];

const FAQS: { q: string; a: string }[] = [
  {
    q: 'Is DEDAN a doctor or a diagnosis?',
    a: 'No. DEDAN provides AI-assisted guidance on how urgent your symptoms may be and what to do next. It does not diagnose conditions and does not replace professional medical care.',
  },
  {
    q: 'What information does DEDAN use?',
    a: 'Only what you provide: your age, sex, optional location and conditions, and the symptoms you describe. Nothing is requested that the assessment does not use.',
  },
  {
    q: 'Where is my assessment stored?',
    a: 'Your assessment history is stored on this device. The assessment itself is sent to the DEDAN service to generate your guidance.',
  },
  {
    q: 'How accurate is the guidance?',
    a: 'DEDAN reports a confidence value for each assessment, but this is not a measure of diagnostic accuracy. The guidance is based only on the information you supplied and cannot rule out a serious condition. If you are worried, seek professional care.',
  },
  {
    q: 'What happens if I am offline?',
    a: 'An assessment cannot be generated offline because it requires the DEDAN service. Your input is preserved so you can send it when your connection returns.',
  },
  {
    q: 'Which languages are supported?',
    a: 'The interface is currently available in English. Clinical guidance language is handled by the assessment service; additional interface translations are shown as unavailable until they are complete.',
  },
];

export const HelpPage: React.FC = () => {
  const [expanded, setExpanded] = useState<number | false>(false);

  return (
    <Section>
      <SectionHeading
        as="h1"
        eyebrow="Help & education"
        title="Understanding how DEDAN works"
        lead="DEDAN helps you decide what to do next when you feel unwell. This page explains what it does, what it does not do, and how to read your guidance."
        maxLead={660}
      />

      {/* ---------------- Urgency levels ---------------- */}
      <Box component="section" aria-labelledby="help-levels" sx={{ mb: { xs: 8, md: 12 } }}>
        <Typography id="help-levels" component="h2" sx={{ fontSize: { xs: '1.375rem', md: '1.625rem' }, fontWeight: 700, letterSpacing: '-0.02em', color: 'text.primary', mb: 1.5 }}>
          What the urgency levels mean
        </Typography>
        <Typography sx={{ fontSize: '1rem', lineHeight: 1.75, color: 'text.secondary', maxWidth: 620, mb: 4 }}>
          Every assessment returns exactly one of these four levels. They describe how quickly you should act —
          not what condition you have.
        </Typography>

        <Box sx={{ maxWidth: 820 }}>
          {LEVELS.map((l) => (
            <Box
              key={l.level}
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: '200px 1fr' },
                gap: { xs: 1.5, md: 4 },
                py: 3.5,
                borderTop: 1,
                borderTopColor: 'divider',
              }}
            >
              <Box>
                <SeverityBadge level={l.level} />
              </Box>
              <Box>
                <Typography sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.primary', mb: 1 }}>
                  {l.body}
                </Typography>
                <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
                  {l.action}
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>

      {/* ---------------- When to seek urgent care ---------------- */}
      <Box
        component="section"
        aria-labelledby="help-urgent"
        sx={{
          mb: { xs: 8, md: 12 },
          p: { xs: 3, md: 5 },
          borderRadius: radius.xl,
          border: `2px solid ${colors.critical.base}`,
          backgroundColor: 'rgba(220,38,38,0.04)',
          maxWidth: 820,
        }}
      >
        <Typography id="help-urgent" component="h2" sx={{ fontSize: { xs: '1.375rem', md: '1.625rem' }, fontWeight: 700, letterSpacing: '-0.02em', color: colors.critical.base, mb: 2 }}>
          Seek emergency care immediately if
        </Typography>
        <Stack component="ul" spacing={1.25} sx={{ m: 0, pl: 2.5 }}>
          {[
            'You have chest pain, or pain spreading to your arm, neck or jaw.',
            'You are struggling to breathe, or breathing is rapidly getting harder.',
            'You have sudden confusion, slurred speech, weakness on one side, or loss of vision.',
            'You have heavy bleeding that will not stop, or you have fainted.',
            'You are having a seizure, or you cannot be woken.',
            'You are pregnant and have severe pain, bleeding, or reduced fetal movement.',
            'You feel your life is in danger, or you are having thoughts of harming yourself.',
          ].map((s) => (
            <Typography component="li" key={s} sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.primary' }}>
              {s}
            </Typography>
          ))}
        </Stack>
        <Typography sx={{ mt: 3, fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
          Do not wait for another assessment. Call your local emergency number.
        </Typography>
      </Box>

      {/* ---------------- Responsible AI ---------------- */}
      <Box component="section" aria-labelledby="help-ai" sx={{ mb: { xs: 8, md: 12 }, maxWidth: 820 }}>
        <Typography id="help-ai" component="h2" sx={{ fontSize: { xs: '1.375rem', md: '1.625rem' }, fontWeight: 700, letterSpacing: '-0.02em', color: 'text.primary', mb: 3 }}>
          Responsible AI
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 4, md: 6 } }}>
          {[
            {
              h: 'Guidance, not diagnosis',
              b: 'DEDAN is not a clinician and does not produce a diagnosis. It estimates urgency and recommends a next step.',
            },
            {
              h: 'Labelled clearly',
              b: 'Where content is AI-generated, it is labelled as such. Where content comes from you, that is labelled too.',
            },
            {
              h: 'Limits are stated',
              b: 'Every result states that it is based only on the information you provided and cannot rule out a serious condition.',
            },
            {
              h: 'No hidden reasoning',
              b: 'DEDAN does not expose or invent step-by-step clinical reasoning. You see the summary, the urgency level and the recommended action.',
            },
          ].map((c) => (
            <Box key={c.h} sx={{ borderTop: 2, borderTopColor: 'primary.main', pt: 2.5 }}>
              <Typography component="h3" sx={{ fontSize: '1rem', fontWeight: 650, color: 'text.primary', mb: 1 }}>
                {c.h}
              </Typography>
              <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'text.secondary' }}>
                {c.b}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* ---------------- FAQ (demoted to the end) ---------------- */}
      <Box component="section" aria-labelledby="help-faq" sx={{ maxWidth: 820 }}>
        <Typography id="help-faq" component="h2" sx={{ fontSize: { xs: '1.375rem', md: '1.625rem' }, fontWeight: 700, letterSpacing: '-0.02em', color: 'text.primary', mb: 3 }}>
          Common questions
        </Typography>
        <Stack spacing={0}>
          {FAQS.map((f, i) => (
            <Accordion
              key={f.q}
              expanded={expanded === i}
              onChange={(_e, isExp) => setExpanded(isExp ? i : false)}
              disableGutters
              elevation={0}
              sx={{
                backgroundColor: 'transparent',
                borderTop: 1,
                borderTopColor: 'divider',
                '&:before': { display: 'none' },
                '&.Mui-expanded': { margin: 0 },
              }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 0, py: 1.5 }}>
                <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: 'text.primary' }}>
                  {f.q}
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ px: 0, pt: 0, pb: 3 }}>
                <Typography sx={{ fontSize: '1rem', lineHeight: 1.75, color: 'text.secondary', maxWidth: 640 }}>
                  {f.a}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Stack>
      </Box>

      {/* ---------------- CTA ---------------- */}
      <Box sx={{ mt: { xs: 8, md: 12 }, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          component={RouterLink}
          to="/assess"
          variant="contained"
          size="large"
          sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
        >
          Start Health Assessment
        </Button>
        <Button
          component={RouterLink}
          to="/consent"
          variant="outlined"
          size="large"
          sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
        >
          How your data is used
        </Button>
      </Box>
    </Section>
  );
};

export default HelpPage;
