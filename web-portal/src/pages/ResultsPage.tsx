/**
 * DEDAN-Health — Triage result
 *
 * Master spec 9 / 16 / 17: this is a clinical-information surface, NOT an API
 * dump. Rules enforced here:
 *
 *  1. Emergency actions appear ABOVE the AI explanation — never buried.
 *  2. One unambiguous urgency level, always labelled in words, never by colour
 *     alone (SeverityBadge renders the label; colour is secondary).
 *  3. Every block is explicitly attributed: what YOU provided vs. what the AI
 *     generated. No implied clinical authority (master spec 15 / 45).
 *  4. Uncertainty is always stated.
 *  5. Only fields the LIVE backend actually returns are rendered
 *     (`backend/models.py::TriageResponse`); nothing is invented.
 */
import React from 'react';
import { Box, Typography, Button, Stack, Link, Divider, Chip, Alert, List, ListItem, ListItemText } from '@mui/material';
import { useNavigate, useLocation, Location } from 'react-router-dom';
import { SeverityBadge } from '../design-system/components';
import { useTranslations } from '../i18n';
import { TriageResponse, TriageLevel, ClinicalGuidanceResponse2, UrgencyLevel } from '../types';
import { useDedanState } from '../state/DedanContext';
import { AssessmentShell } from '../components/assessment/AssessmentShell';
import { colors, radius } from '../design-system/tokens';

interface LocationState { response?: TriageResponse | ClinicalGuidanceResponse2; session_id?: string }

/** i18n key for each urgency level's headline. */
const tKey: Record<TriageLevel, 'emergency' | 'urgent' | 'routine' | 'selfCare'> = {
  emergency: 'emergency',
  urgent: 'urgent',
  routine: 'routine',
  self_care: 'selfCare',
};

/** Level -> semantic token, so severity colour is defined in ONE place. */
const levelColor: Record<TriageLevel, { base: string; tint: string }> = {
  emergency: { base: colors.critical.base, tint: 'rgba(220,38,38,0.06)' },
  urgent: { base: colors.warning.base, tint: 'rgba(180,83,9,0.06)' },
  routine: { base: colors.info.base, tint: 'rgba(37,99,235,0.05)' },
  self_care: { base: colors.success.base, tint: 'rgba(21,128,61,0.05)' },
};

const urgencyColor: Record<UrgencyLevel, { base: string; tint: string }> = {
  emergency: { base: colors.critical.base, tint: 'rgba(220,38,38,0.06)' },
  urgent: { base: colors.warning.base, tint: 'rgba(180,83,9,0.06)' },
  routine: { base: colors.info.base, tint: 'rgba(37,99,235,0.05)' },
  soon: { base: colors.warning.base, tint: 'rgba(180,83,9,0.06)' },
};

/** A labelled result block. Keeps the information hierarchy identical for every level. */
const Block: React.FC<{
  label: string;
  attribution?: string;
  children: React.ReactNode;
  emphasis?: boolean;
}> = ({ label, attribution, children, emphasis }) => (
  <Box
    component="section"
    sx={{
      py: 3.5,
      borderTop: 1,
      borderTopColor: 'divider',
      ...(emphasis ? {} : {}),
    }}
  >
    <Typography
      component="h3"
      sx={{
        fontSize: '0.8125rem',
        fontWeight: 700,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'text.secondary',
        mb: attribution ? 0.5 : 1.5,
      }}
    >
      {label}
    </Typography>
    {attribution && (
      <Typography component="p" sx={{ fontSize: '0.8125rem', color: 'text.secondary', opacity: 0.85, mb: 1.5 }}>
        {attribution}
      </Typography>
    )}
    {children}
  </Box>
);

/** Check if response is the new v2 clinical guidance format */
const isClinicalGuidanceResponse = (
  response: TriageResponse | ClinicalGuidanceResponse2
): response is ClinicalGuidanceResponse2 => {
  return 'clinical_response' in response && 'safety' in (response as ClinicalGuidanceResponse2).clinical_response;
};

export const ResultsCard: React.FC<{ response: TriageResponse; onNew: () => void }> = ({
  response,
  onNew,
}) => {
  const { t } = useTranslations();
  const navigate = useNavigate();
  const isEmergency = response.triage_level === 'emergency';
  const level = levelColor[response.triage_level];
  const heading = t(`results.${tKey[response.triage_level]}`);
  const contacts = response.emergency_contacts ?? [];

  return (
    <Stack spacing={0}>
      {/* ============ SAFETY FIRST: emergency surface, above all AI text ============ */}
      {isEmergency && (
        <Box
          role="alert"
          aria-live="assertive"
          sx={{
            border: `2px solid ${colors.critical.base}`,
            backgroundColor: level.tint,
            borderRadius: radius.xl,
            p: { xs: 3, md: 4 },
            mb: 5,
          }}
        >
          <Typography
            component="h2"
            sx={{
              fontSize: { xs: '1.5rem', md: '1.875rem' },
              lineHeight: 1.15,
              fontWeight: 800,
              letterSpacing: '-0.02em',
              color: colors.critical.base,
              mb: 1.5,
            }}
          >
            {heading}
          </Typography>
          <Typography sx={{ fontSize: '1.125rem', lineHeight: 1.65, color: 'text.primary', mb: 3, maxWidth: 640 }}>
            Your responses indicate that you may need immediate medical attention.
          </Typography>

          <Typography
            component="h3"
            sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: colors.critical.base, mb: 1.5 }}
          >
            {t('results.whatToDoNow')}
          </Typography>
          <Stack component="ul" spacing={1} sx={{ m: 0, pl: 2.5, mb: contacts.length ? 3 : 0 }}>
            <Typography component="li" sx={{ fontSize: '1rem', lineHeight: 1.6 }}>
              Contact your local emergency number immediately.
            </Typography>
            <Typography component="li" sx={{ fontSize: '1rem', lineHeight: 1.6 }}>
              Go to the nearest emergency department, or ask someone to take you there.
            </Typography>
            <Typography component="li" sx={{ fontSize: '1rem', lineHeight: 1.6 }}>
              Do not drive yourself if you feel unwell.
            </Typography>
          </Stack>

          {contacts.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography component="h3" sx={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'text.secondary', mb: 1 }}>
                Emergency contacts
              </Typography>
              <Stack spacing={0.5}>
                {contacts.map((c) => (
                  <Link
                    key={c}
                    href={`tel:${c.replace(/[^+\d]/g, '')}`}
                    sx={{ fontSize: '1.125rem', fontWeight: 600, color: 'text.primary', textDecorationColor: 'currentColor' }}
                  >
                    {c}
                  </Link>
                ))}
              </Stack>
            </Box>
          )}

          {contacts.length > 0 && (
            <Button
              href={`tel:${contacts[0].replace(/[^+\d]/g, '')}`}
              variant="contained"
              size="large"
              sx={{
                mt: 3.5,
                px: 4,
                py: 1.5,
                borderRadius: radius.pill,
                backgroundColor: colors.critical.base,
                '&:hover': { backgroundColor: '#B91C1C' },
              }}
            >
              {t('results.callEmergency')}
            </Button>
          )}
        </Box>
      )}

      {/* ============ HEADER ============ */}
      {!isEmergency && (
        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 1.5 }}>
            <SeverityBadge level={response.triage_level} />
          </Box>
          <Typography
            component="h2"
            sx={{
              fontSize: { xs: '1.75rem', md: '2.25rem' },
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              fontWeight: 750,
              color: 'text.primary',
            }}
          >
            {heading}
          </Typography>
          <Typography sx={{ mt: 1.5, fontSize: '1.0625rem', lineHeight: 1.65, color: 'text.secondary', maxWidth: 640 }}>
            {response.triage_level === 'urgent'
              ? 'Your responses suggest that you should seek medical evaluation soon.'
              : 'Based on the information provided, your symptoms do not currently indicate an immediate emergency.'}
          </Typography>
        </Box>
      )}

      {/* ============ ASSESSMENT SUMMARY ============ */}
      <Block label={t('results.summary')} attribution={t('results.providedByYou')}>
        <Typography sx={{ fontSize: '1.0625rem', lineHeight: 1.7, color: 'text.primary' }}>
          {response.patient_summary}
        </Typography>
      </Block>

      {/* ============ NEXT STEP ============ */}
      <Block label={t('results.nextStep')} emphasis>
        <Typography sx={{ fontSize: '1.0625rem', lineHeight: 1.7, color: 'text.primary', fontWeight: 500 }}>
          {response.suggested_next_step}
        </Typography>
      </Block>

      {/* ============ WHAT THE AI NOTICED ============ */}
      <Block label={t('results.whatWeNoticed')} attribution={t('results.generatedByAi')}>
        {response.risk_flags.length === 0 ? (
          <Typography sx={{ fontSize: '1rem', lineHeight: 1.7, color: 'text.secondary' }}>
            {t('results.riskFlagsEmpty')}
          </Typography>
        ) : (
          <Stack component="ul" spacing={1.5} sx={{ m: 0, pl: 2.5 }}>
            {response.risk_flags.map((f, i) => (
              <Box component="li" key={`${f.type}-${i}`}>
                <Typography component="span" sx={{ fontSize: '0.9375rem', fontWeight: 600, color: 'text.primary' }}>
                  {f.description}
                </Typography>
                <Typography component="span" sx={{ fontSize: '0.9375rem', color: 'text.secondary' }}>
                  {' '}({f.severity})
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Block>

      {/* ============ FOLLOW-UP ============ */}
      {response.follow_up_timeframe && (
        <Block label={t('results.followUpLabel')}>
          <Typography sx={{ fontSize: '1.0625rem', lineHeight: 1.7, color: 'text.primary' }}>
            {response.follow_up_timeframe}
          </Typography>
        </Block>
      )}

      {/* ============ WHEN TO ESCALATE ============ */}
      <Block label={t('results.whenToSeek')}>
        <Typography sx={{ fontSize: '1rem', lineHeight: 1.75, color: 'text.secondary', maxWidth: 640 }}>
          {t('results.whenToSeekEmergencyBody')}
        </Typography>
      </Block>

      {/* ============ LIMITS + DISCLAIMER ============ */}
      <Box sx={{ py: 3.5, borderTop: 1, borderTopColor: 'divider' }}>
        <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.75, color: 'text.secondary', maxWidth: 640 }}>
          {t('results.uncertainty')}
        </Typography>
        <Typography sx={{ mt: 2, fontSize: '0.875rem', lineHeight: 1.7, color: 'text.secondary', opacity: 0.9, maxWidth: 640 }}>
          {response.disclaimer}
        </Typography>
        <Typography sx={{ mt: 2, fontSize: '0.8125rem', color: 'text.secondary', opacity: 0.8 }}>
          {t('results.confidence')}: {Math.round(response.confidence_score * 100)}% — {t('results.confidenceNote')}
        </Typography>
      </Box>

      {/* ============ ACTIONS ============ */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        sx={{ pt: 1 }}
        divider={<Divider orientation="vertical" flexItem />}
      >
        <Button
          variant="contained"
          size="large"
          onClick={onNew}
          sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
        >
          {t('results.newAssessment')}
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => navigate('/history')}
          sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
        >
          {t('results.viewHistory')}
        </Button>
      </Stack>
    </Stack>
  );
};

/** ClinicalGuidanceResponse2 Results Card — structured clinical guidance */
export const ClinicalResultsCard: React.FC<{
  response: ClinicalGuidanceResponse2;
  onNew: () => void;
}> = ({ response, onNew }) => {
  const { t } = useTranslations();
  const navigate = useNavigate();
  const safety = response.clinical_response?.safety;
  const urgency = safety?.urgency as UrgencyLevel || 'routine';
  const uc = urgencyColor[urgency];
  const cr = response.clinical_response;

  return (
    <Stack spacing={0}>
      {/* ============ SAFETY FIRST ============ */}
      <Alert
        severity={urgency === 'emergency' ? 'error' : urgency === 'urgent' ? 'warning' : 'info'}
        sx={{ mb: 3, borderRadius: radius.lg }}
        action={<Chip label={urgency.toUpperCase()} size="small" color={urgency === 'emergency' ? 'error' : urgency === 'urgent' ? 'warning' : 'info'} sx={{ ml: 1 }} />}
      >
        <Typography sx={{ fontWeight: 600 }}>
          {safety?.emergency_message || safety?.recommended_action || 'Assessment complete'}
        </Typography>
        {safety?.red_flags && safety.red_flags.length > 0 && (
          <List dense sx={{ mt: 1 }}>
            {safety.red_flags.map((flag: string, i: number) => (
              <ListItem key={i}><ListItemText primary={flag} /></ListItem>
            ))}
          </List>
        )}
      </Alert>

      {/* ============ HEALTH SUMMARY ============ */}
      <Block label="Health Summary" attribution="What you told us">
        <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.75, color: 'text.primary' }}>
          {cr.health_summary.symptoms.join(', ') || 'No symptoms reported'}
        </Typography>
        <Typography sx={{ mt: 1, fontSize: '0.875rem', color: 'text.secondary' }}>
          Duration: {cr.health_summary.duration} | Severity: {cr.health_summary.severity}
        </Typography>
        {cr.health_summary.relevant_history && cr.health_summary.relevant_history.length > 0 && (
          <Typography sx={{ mt: 1, fontSize: '0.875rem', color: 'text.secondary' }}>
            History: {cr.health_summary.relevant_history.join('; ')}
          </Typography>
        )}
      </Block>

      {/* ============ SYMPTOM ANALYSIS ============ */}
      {cr.possible_explanations && cr.possible_explanations.length > 0 && (
        <Block label="What may be happening" attribution="AI-generated possible explanations">
          {cr.possible_explanations.map((pe: any, i: number) => (
            <Box key={i} sx={{ mb: 2, p: 2, borderRadius: radius.md, backgroundColor: 'background.paper' }}>
              <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>{pe.label}</Typography>
              <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', mt: 0.5 }}>Why it fits: {pe.why_it_fits}</Typography>
              <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>What does not fit: {pe.what_does_not_fit}</Typography>
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7, mt: 0.5 }}>
                Evidence: {pe.evidence_level} | Missing: {pe.requires_more_info.join(', ')}
              </Typography>
            </Box>
          ))}
          {cr.uncertainty && (
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', fontStyle: 'italic' }}>
              Uncertainty: {cr.uncertainty.message} (Level: {cr.uncertainty.level})
            </Typography>
          )}
        </Block>
      )}

      {/* ============ BODY MECHANISM ============ */}
      {cr.body_mechanism && cr.body_mechanism.length > 0 && (
        <Block label="What is happening in your body" attribution="AI-generated explanation of disease mechanism">
          {cr.body_mechanism.map((bm: any, i: number) => (
            <Box key={i} sx={{ mb: 2, p: 2, borderRadius: radius.md, backgroundColor: 'background.paper', borderLeft: '3px solid', borderLeftColor: 'primary.main' }}>
              <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'primary.main' }}>
                Step {bm.step_number}: {bm.title}
              </Typography>
              <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', mt: 0.5 }}>
                {bm.description}
              </Typography>
              {bm.visual_reference && (
                <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7, mt: 0.5 }}>
                  Visual reference: {bm.visual_reference}
                </Typography>
              )}
            </Box>
          ))}
        </Block>
      )}

      {/* ============ VISUAL EDUCATION ============ */}
      {cr.visual_education && cr.visual_education.length > 0 && (
        <Block label="Understand your condition" attribution="Educational visuals from authoritative sources">
          {cr.visual_education.map((ve: any, i: number) => (
            <Box key={i} sx={{ mb: 2, p: 2, borderRadius: radius.md, backgroundColor: 'background.paper', border: '1px solid', borderColor: 'divider' }}>
              <Typography sx={{ fontSize: '1rem', fontWeight: 600 }}>{ve.title}</Typography>
              <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>{ve.description}</Typography>
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
                Source: {ve.source} | {ve.visual_type}
                {ve.source_url && ` | ${ve.source_url}`}
                {ve.license && ` | License: ${ve.license}`}
                {ve.is_ai_generated && ' | AI-generated educational illustration — not a clinical photograph'}
                {ve.ai_disclaimer && ` | ${ve.ai_disclaimer}`}
              </Typography>
            </Box>
          ))}
        </Block>
      )}

      {/* ============ TREATMENT APPROACH ============ */}
      {cr.treatment_approach && (
        <Block label="Treatment approach" attribution="AI-generated treatment explanation">
          <Box sx={{ p: 2, borderRadius: radius.md, backgroundColor: 'background.paper', border: '1px solid', borderColor: 'primary.light' }}>
            <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary', mb: 1 }}>
              Treatment Goal: {cr.treatment_approach.goal}
            </Typography>
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', mb: 1 }}>
              How it works: {cr.treatment_approach.mechanism}
            </Typography>
            {cr.treatment_approach.patient_actions && cr.treatment_approach.patient_actions.length > 0 && (
              <>
                <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
                  What you can do:
                </Typography>
                <List dense sx={{ mb: 1 }}>
                  {cr.treatment_approach.patient_actions.map((action: string, i: number) => (
                    <ListItem key={i}><ListItemText primary={action} /></ListItem>
                  ))}
                </List>
              </>
            )}
            {cr.treatment_approach.professional_actions && cr.treatment_approach.professional_actions.length > 0 && (
              <>
                <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
                  What requires a clinician:
                </Typography>
                <List dense sx={{ mb: 1 }}>
                  {cr.treatment_approach.professional_actions.map((action: string, i: number) => (
                    <ListItem key={i}><ListItemText primary={action} /></ListItem>
                  ))}
                </List>
              </>
            )}
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', mb: 0.5 }}>
              Expected improvement: {cr.treatment_approach.expected_improvement}
            </Typography>
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary', mb: 1 }}>
              Timeline: {cr.treatment_approach.timeline}
            </Typography>
            {cr.treatment_approach.warning_signs && cr.treatment_approach.warning_signs.length > 0 && (
              <>
                <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'error.main', mb: 0.5 }}>
                  Warning signs to watch for:
                </Typography>
                <List dense sx={{ mb: 1 }}>
                  {cr.treatment_approach.warning_signs.map((ws: string, i: number) => (
                    <ListItem key={i}><ListItemText primary={ws} /></ListItem>
                  ))}
                </List>
              </>
            )}
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
              Evidence: {cr.treatment_approach.evidence_level}
              {cr.treatment_approach.sources && cr.treatment_approach.sources.length > 0 && (
                <> | Sources: {cr.treatment_approach.sources.map(s => s.title).join(', ')}</>
              )}
            </Typography>
          </Box>
        </Block>
      )}

      {/* ============ TREATMENT EDUCATION ============ */}
      <Block label="How treatment works" attribution="AI-generated treatment education">
        {cr.treatment_education.map((te: any, i: number) => (
          <Box key={i} sx={{ mb: 2, p: 2, borderRadius: radius.md, backgroundColor: 'background.paper' }}>
            <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>{te.title}</Typography>
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>{te.description}</Typography>
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>Why it may help: {te.why_it_may_help}</Typography>
            <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>Expected timeline: {te.expected_timeline}</Typography>
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
              Evidence: {te.evidence_level} | Monitor: {te.what_to_monitor} | Reassess: {te.when_to_reassess}
            </Typography>
          </Box>
        ))}
      </Block>

      {/* ============ MEDICATION SAFETY ============ */}
      {cr.medication_information && cr.medication_information.length > 0 && (
        <Block label="Medication information to discuss with a pharmacist/clinician" attribution="Educational only — not a prescription">
          {cr.medication_information.map((mi: any, i: number) => (
            <Box key={i} sx={{ mb: 2, p: 2, borderRadius: radius.md, backgroundColor: 'background.paper', border: '1px solid', borderColor: 'warning.light' }}>
              <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: 'warning.dark' }}>
                {mi.medication_name} ({mi.medication_class})
              </Typography>
              <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>Purpose: {mi.general_purpose}</Typography>
              <Typography sx={{ fontSize: '0.8125rem', color: 'text.secondary' }}>
                Warnings: {mi.common_warnings.join('; ') || 'None listed'}
              </Typography>
              <Typography sx={{ fontSize: '0.8125rem', color: 'text.secondary' }}>
                Interactions: {mi.potential_interactions.join('; ') || 'None listed'}
              </Typography>
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
                Ask pharmacist: {mi.questions_to_ask.join('; ')}
              </Typography>
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
                Check package: {mi.package_check_items.join('; ')}
              </Typography>
              <Chip label="Educational information only" size="small" variant="outlined" color="warning" sx={{ mt: 1 }} />
            </Box>
          ))}
        </Block>
      )}

      {/* ============ MEDICATION VERIFICATION ============ */}
      {cr.medication_verification && cr.medication_verification.length > 0 && (
        <Block label="What to verify at the pharmacy" attribution="Pharmacy verification checklist">
          {cr.medication_verification.map((mv: any, i: number) => (
            <Box key={i} sx={{ mb: 1, p: 1.5, borderRadius: radius.sm, backgroundColor: 'background.paper', borderLeft: '3px solid', borderLeftColor: 'info.main' }}>
              <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'info.dark' }}>
                {mv.field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
              </Typography>
              <Typography sx={{ fontSize: '0.8125rem', color: 'text.secondary' }}>{mv.description}</Typography>
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
                Why important: {mv.why_important}
              </Typography>
            </Box>
          ))}
        </Block>
      )}

      {/* ============ WARNING SIGNS ============ */}
      {cr.warning_signs && cr.warning_signs.length > 0 && (
        <Block label="Warning signs — seek care immediately if these occur" attribution="AI-generated warning signs">
          <Alert severity="warning" sx={{ mb: 1, borderRadius: radius.lg }}>
            <List dense>
              {cr.warning_signs.map((ws: string, i: number) => (
                <ListItem key={i}><ListItemText primary={ws} /></ListItem>
              ))}
            </List>
          </Alert>
        </Block>
      )}

      {/* ============ NEXT STEPS ============ */}
      {cr.next_steps && Object.keys(cr.next_steps).length > 0 && (
        <Block label="What to do next" attribution="AI-generated action plan">
          {Object.entries(cr.next_steps).map(([timeframe, steps]) => (
            <Box key={timeframe} sx={{ mb: 2, p: 2, borderRadius: radius.md, backgroundColor: 'background.paper' }}>
              <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: 'primary.main', textTransform: 'capitalize', mb: 1 }}>
                {timeframe.replace(/_/g, ' ')}
              </Typography>
              <List dense sx={{ pl: 1 }}>
                {steps.map((step: string, i: number) => (
                  <ListItem key={i}><ListItemText primary={step} /></ListItem>
                ))}
              </List>
            </Box>
          ))}
        </Block>
      )}

      {/* ============ FOLLOW-UP ============ */}
      <Block label="Follow-up" attribution="AI-generated guidance">
        <Typography sx={{ fontSize: '0.9375rem', lineHeight: 1.75, color: 'text.primary' }}>
          {cr.follow_up?.recommended ? 'Follow-up recommended' : 'No follow-up needed'}
        </Typography>
        {cr.follow_up?.timeframe && (
          <Typography sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>Timeframe: {cr.follow_up.timeframe}</Typography>
        )}
        {cr.follow_up?.warning_signs && (
          <List dense>
            {cr.follow_up.warning_signs.map((ws: string, i: number) => (
              <ListItem key={i}><ListItemText primary={ws} /></ListItem>
            ))}
          </List>
        )}
      </Block>

      {/* ============ SOURCES ============ */}
      {cr.sources && cr.sources.length > 0 && (
        <Block label="Sources" attribution="Evidence-based">
          {cr.sources.map((s: any, i: number) => (
            <Typography key={i} sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
              {s.title} ({s.type}) — {s.jurisdiction}
            </Typography>
          ))}
        </Block>
      )}

      {/* ============ DISCLAIMER ============ */}
      <Box sx={{ py: 3.5, borderTop: 1, borderTopColor: 'divider' }}>
        <Typography sx={{ fontSize: '0.875rem', lineHeight: 1.75, color: 'text.secondary' }}>
          {cr.disclaimer}
        </Typography>
        <Typography sx={{ mt: 1, fontSize: '0.8125rem', color: 'text.secondary', opacity: 0.8 }}>
          Confidence: {Math.round(response.clinical_response.confidence_score * 100)}% | Provider: {response.provider} | Model: {response.model}
        </Typography>
        {response.professional_review && (
          <Alert severity="info" sx={{ mt: 2, borderRadius: radius.lg }}>
            <Typography sx={{ fontWeight: 600 }}>Professional Review Recommended</Typography>
            <Typography>This assessment requires review by a healthcare professional.</Typography>
            {response.professional_review_reason && (
              <Typography sx={{ mt: 0.5, fontSize: '0.875rem', color: 'text.secondary' }}>
                Reason: {response.professional_review_reason}
              </Typography>
            )}
          </Alert>
        )}
        {response.safety_flags && response.safety_flags.length > 0 && (
          <Typography sx={{ mt: 1, fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
            Safety flags: {response.safety_flags.join(', ')}
          </Typography>
        )}
      </Box>

      {/* ============ ACTIONS ============ */}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ pt: 1 }} divider={<Divider orientation="vertical" flexItem />}>
        <Button variant="contained" size="large" onClick={onNew} sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}>
          {t('results.newAssessment')}
        </Button>
        <Button variant="outlined" size="large" onClick={() => navigate('/history')} sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}>
          {t('results.viewHistory')}
        </Button>
      </Stack>
    </Stack>
  );
};

export const ResultsPage: React.FC = () => {
  const { t } = useTranslations();
  const location = useLocation() as Location<LocationState>;
  const navigate = useNavigate();
  const { sessionId } = useDedanState();
  const response = location.state?.response;

  if (!response) {
    return (
      <AssessmentShell
        title={t('results.noResultsTitle')}
        lead={t('results.noResultsBody')}
        actions={
          <>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/history')}
              sx={{ px: 4, py: 1.5, borderRadius: radius.pill, borderColor: 'divider', color: 'text.primary' }}
            >
              {t('results.viewHistory')}
            </Button>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/assess')}
              sx={{ px: 4, py: 1.5, borderRadius: radius.pill }}
            >
              {t('results.startAssessment')}
            </Button>
          </>
        }
      />
    );
  }

  return (
    <Box
      sx={{
        width: '100%',
        backgroundColor: 'background.default',
        pb: { xs: 8, md: 12 },
      }}
    >
      <Box sx={{ maxWidth: 960, mx: 'auto', width: '100%', px: { xs: 3, md: 6 }, pt: { xs: 6, md: 10 } }}>
        <Typography
          component="p"
          sx={{
            mb: 4,
            fontSize: '0.8125rem',
            fontWeight: 700,
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: 'primary.main',
          }}
        >
          {t('results.yourGuidance')}
        </Typography>
        {isClinicalGuidanceResponse(response) ? (
          <ClinicalResultsCard response={response} onNew={() => navigate('/assess')} />
        ) : (
          <ResultsCard response={response} onNew={() => navigate('/assess')} />
        )}
        <Typography sx={{ mt: 4, fontSize: '0.75rem', color: 'text.secondary', opacity: 0.7 }}>
          Session {sessionId}
        </Typography>
      </Box>
    </Box>
  );
};

export default ResultsPage;
