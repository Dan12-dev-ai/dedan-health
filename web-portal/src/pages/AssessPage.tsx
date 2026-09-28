/**
 * DEDAN-Health — Assessment: patient context (step 1 of 2)
 *
 * Master spec 8: a calm, guided assessment rather than an exposed form.
 *
 * Composition: PROGRESS -> QUESTION -> EXPLANATION -> INPUT -> BACK/CONTINUE
 *
 * Every field below maps to a field the LIVE backend actually consumes
 * (`backend/models.py::PatientProfile`). Nothing here is decorative:
 *   age                -> PatientProfile.age
 *   sex                -> PatientProfile.sex
 *   pregnancy_status   -> PatientProfile.pregnancy_status
 *   chronic_conditions -> PatientProfile.chronic_conditions
 *   language           -> PatientProfile.language
 *   location           -> PatientProfile.location
 *
 * Accessibility: real labels, described-by helper text, aria-invalid on error,
 * keyboard-operable controls, and errors that never clear user input.
 */
import React, { useMemo, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  FormHelperText,
  FormControlLabel,
  Switch,
  Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTranslations } from '../i18n';
import { useDedanState } from '../state/DedanContext';
import { PatientProfile, Language, Sex } from '../types';
import { AssessmentShell } from '../components/assessment/AssessmentShell';
import { colors, radius } from '../design-system/tokens';

/** Long-term conditions offered. Sent verbatim to the backend as strings. */
const CHRONIC_OPTIONS = [
  'Diabetes',
  'Hypertension',
  'Asthma',
  'Heart Disease',
  'COPD',
  'Kidney Disease',
  'HIV',
  'Tuberculosis',
];

/**
 * Only `en` has a complete catalog today. The others are listed but disabled so
 * the UI never implies a translation exists when it does not (master spec 46).
 */
const LANGUAGES: { value: Language; label: string; available: boolean }[] = [
  { value: 'en', label: 'English', available: true },
  { value: 'sw', label: 'Kiswahili', available: false },
  { value: 'am', label: 'አማርኛ (Amharic)', available: false },
  { value: 'es', label: 'Español', available: false },
  { value: 'fr', label: 'Français', available: false },
];

/** Local (string-based) form state so an empty age is never coerced to 0. */
interface FormState {
  age: string;
  sex: Sex | '';
  location: string;
  pregnancy_status: boolean;
  chronic_conditions: string[];
  language: Language;
}

const empty = (): FormState => ({
  age: '',
  sex: '',
  location: '',
  pregnancy_status: false,
  chronic_conditions: [],
  language: 'en',
});

const fromProfile = (p: PatientProfile | null): FormState =>
  p
    ? {
        age: p.age === '' || p.age === undefined || p.age === null ? '' : String(p.age),
        sex: p.sex ?? '',
        location: p.location ?? '',
        pregnancy_status: Boolean(p.pregnancy_status),
        chronic_conditions: p.chronic_conditions ?? [],
        language: p.language ?? 'en',
      }
    : empty();

/** Shared field label style — larger and softer than a default form label. */
const fieldLabel = {
  display: 'block',
  mb: 1,
  fontSize: '0.9375rem',
  fontWeight: 600,
  color: 'text.primary',
} as const;

const helpText = {
  mt: 1,
  fontSize: '0.875rem',
  color: 'text.secondary',
} as const;

export const AssessPage: React.FC = () => {
  const { t } = useTranslations();
  const { profile: saved, setProfile } = useDedanState();
  const navigate = useNavigate();

  const [form, setForm] = useState<FormState>(() => fromProfile(saved));
  const [errors, setErrors] = useState<{ age?: string; sex?: string }>({});

  const patch = (p: Partial<FormState>) => setForm((f) => ({ ...f, ...p }));

  const toggleCondition = (c: string) =>
    patch({
      chronic_conditions: form.chronic_conditions.includes(c)
        ? form.chronic_conditions.filter((x) => x !== c)
        : [...form.chronic_conditions, c],
    });

  const validate = (): boolean => {
    const e: { age?: string; sex?: string } = {};
    const ageNum = Number(form.age);
    if (form.age.trim() === '' || Number.isNaN(ageNum) || ageNum < 0 || ageNum > 120) {
      e.age = t('profile.ageError');
    }
    if (!form.sex) e.sex = t('profile.sexError');
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      // Move focus to the first invalid control so keyboard/SR users are told.
      const firstInvalid = document.querySelector<HTMLElement>('[aria-invalid="true"]');
      firstInvalid?.focus();
      return;
    }
    const clean: PatientProfile = {
      age: Number(form.age),
      sex: form.sex as Sex,
      location: form.location.trim() || undefined,
      pregnancy_status: form.sex === 'female' ? form.pregnancy_status : false,
      chronic_conditions: form.chronic_conditions,
      language: form.language,
    };
    setProfile(clean);
    navigate('/triage');
  };

  const showPregnancy = form.sex === 'female';
  const ageErrorId = 'assess-age-error';
  const sexErrorId = 'assess-sex-error';

  const selectedChronic = useMemo(
    () => form.chronic_conditions.join(', '),
    [form.chronic_conditions],
  );

  return (
    <AssessmentShell
      progress={{ current: 1, total: 2, labelTemplate: t('assess.step') }}
      title={t('assess.step1Title')}
      lead={t('assess.step1Lead')}
      notice={t('assess.reviewNotice')}
      actions={
        <>
          <Button
            type="button"
            variant="outlined"
            size="large"
            onClick={() => navigate('/')}
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: radius.pill,
              borderColor: 'divider',
              color: 'text.primary',
              flexShrink: 0,
            }}
          >
            {t('assess.back')}
          </Button>
          <Button
            type="submit"
            form="assess-form"
            variant="contained"
            size="large"
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: radius.pill,
              flexGrow: { xs: 1, sm: 0 },
            }}
          >
            {t('assess.continue')}
          </Button>
        </>
      }
    >
      <Box
        id="assess-form"
        component="form"
        onSubmit={handleSubmit}
        noValidate
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
          columnGap: 4,
          rowGap: 5,
        }}
      >
        {/* ---- Age ---- */}
        <Box>
          <Typography component="label" htmlFor="assess-age" sx={fieldLabel}>
            {t('profile.age')}
          </Typography>
          <TextField
            id="assess-age"
            type="number"
            fullWidth
            value={form.age}
            onChange={(e) => patch({ age: e.target.value })}
            error={Boolean(errors.age)}
            inputProps={{ min: 0, max: 120, inputMode: 'numeric', 'aria-describedby': ageErrorId }}
            placeholder="e.g. 34"
            sx={{ '& .MuiOutlinedInput-root': { borderRadius: radius.lg } }}
          />
          <Typography id={ageErrorId} component="p" sx={{ ...helpText, color: errors.age ? 'error.main' : 'text.secondary' }}>
            {errors.age ?? t('assess.ageHelp')}
          </Typography>
        </Box>

        {/* ---- Sex ---- */}
        <Box>
          <Typography component="span" id="assess-sex-label" sx={fieldLabel}>
            {t('profile.sex')}
          </Typography>
          <ToggleButtonGroup
            value={form.sex}
            exclusive
            fullWidth
            aria-labelledby="assess-sex-label"
            onChange={(_e, v: Sex | null) => patch({ sex: v ?? '', pregnancy_status: v === 'female' ? form.pregnancy_status : false })}
            sx={{
              '& .MuiToggleButton-root': {
                borderRadius: radius.lg,
                py: 1.5,
                textTransform: 'none',
                borderColor: 'divider',
                '&.Mui-selected': {
                  backgroundColor: 'rgba(46,125,50,0.10)',
                  color: colors.brand.primary,
                  fontWeight: 600,
                  borderColor: colors.brand.primary,
                },
              },
            }}
          >
            <ToggleButton value="female" aria-describedby={sexErrorId}>{t('profile.female')}</ToggleButton>
            <ToggleButton value="male" aria-describedby={sexErrorId}>{t('profile.male')}</ToggleButton>
            <ToggleButton value="other" aria-describedby={sexErrorId}>{t('profile.other')}</ToggleButton>
          </ToggleButtonGroup>
          <Typography id={sexErrorId} component="p" sx={{ ...helpText, color: errors.sex ? 'error.main' : 'text.secondary' }}>
            {errors.sex ?? t('assess.sexHelp')}
          </Typography>
        </Box>

        {/* ---- Pregnancy (conditional, only when relevant) ---- */}
        {showPregnancy && (
          <Box sx={{ gridColumn: { sm: '1 / -1' } }}>
            <FormControlLabel
              control={
                <Switch
                  checked={form.pregnancy_status}
                  onChange={(e) => patch({ pregnancy_status: e.target.checked })}
                />
              }
              label={t('profile.pregnancy')}
              sx={{ ml: 0, gap: 1, '& .MuiFormControlLabel-label': { fontSize: '0.9375rem', color: 'text.primary' } }}
            />
          </Box>
        )}

        {/* ---- Location ---- */}
        <Box>
          <Typography component="label" htmlFor="assess-location" sx={fieldLabel}>
            {t('profile.location')}
          </Typography>
          <TextField
            id="assess-location"
            fullWidth
            value={form.location}
            onChange={(e) => patch({ location: e.target.value })}
            placeholder="City, region or country"
            inputProps={{ 'aria-describedby': 'assess-location-help' }}
            sx={{ '& .MuiOutlinedInput-root': { borderRadius: radius.lg } }}
          />
          <Typography id="assess-location-help" component="p" sx={helpText}>
            {t('assess.locationHelp')}
          </Typography>
        </Box>

        {/* ---- Language ---- */}
        <Box>
          <Typography component="label" htmlFor="assess-language" id="assess-language-label" sx={fieldLabel}>
            {t('profile.language')}
          </Typography>
          <FormControl fullWidth>
            <Select
              id="assess-language"
              labelId="assess-language-label"
              value={form.language}
              onChange={(e) => patch({ language: e.target.value as Language })}
              sx={{ borderRadius: radius.lg }}
              inputProps={{ 'aria-describedby': 'assess-language-help' }}
            >
              {LANGUAGES.map((l) => (
                <MenuItem key={l.value} value={l.value} disabled={!l.available}>
                  {l.label}{!l.available ? ' — unavailable' : ''}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Typography id="assess-language-help" component="p" sx={helpText}>
            {t('assess.languageHelp')}
          </Typography>
        </Box>

        {/* ---- Chronic conditions ---- */}
        <Box sx={{ gridColumn: { sm: '1 / -1' } }}>
          <Typography component="h2" sx={fieldLabel}>
            {t('profile.chronic')}
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.25 }} role="group" aria-label={t('profile.chronic')}>
            {CHRONIC_OPTIONS.map((c) => {
              const selected = form.chronic_conditions.includes(c);
              return (
                <Chip
                  key={c}
                  label={c}
                  onClick={() => toggleCondition(c)}
                  aria-pressed={selected}
                  sx={{
                    px: 1,
                    py: 2.25,
                    fontSize: '0.9375rem',
                    borderRadius: radius.pill,
                    border: '1px solid',
                    borderColor: selected ? colors.brand.primary : 'divider',
                    backgroundColor: selected ? 'rgba(46,125,50,0.10)' : 'transparent',
                    color: selected ? colors.brand.primary : 'text.secondary',
                    fontWeight: selected ? 600 : 500,
                  }}
                />
              );
            })}
          </Box>
          <Typography component="p" sx={helpText}>
            {selectedChronic ? `${t('profile.chronic')}: ${selectedChronic}` : t('assess.chronicHelp')}
          </Typography>
        </Box>
      </Box>
    </AssessmentShell>
  );
};

export default AssessPage;
