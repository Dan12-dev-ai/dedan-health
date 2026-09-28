/** English (live) UI message catalog. Mirrors backend Language.ENGLISH. */
export const en = {
  nav: {
    home: 'Home',
    assess: 'Assess',
    history: 'History',
    followUp: 'Follow-Up',
    help: 'Help',
    profile: 'Profile',
    settings: 'Settings',
    pricing: 'Pricing',
  },
  home: {
    hero: 'Health guidance,\ndesigned around you.',
    sub: "Understand what your symptoms may mean and find the next step with clear, responsible health guidance.",
    cta: 'Start Health Assessment',
    viewHistory: 'View History',
    findCare: 'Find Care',
    learn: 'Learn How It Works',
    trusted: 'Trusted healthcare intelligence, delivered clearly and responsibly.',
  },
  /**
   * Landing-page copy (master spec 6: home page composition).
   * Kept as one namespace so the marketing surface can be re-authored or
   * localised without touching component code.
   */
  landing: {
    eyebrow: 'DEDAN HEALTH',
    trustEyebrow: 'Our responsibility',
    trustTitle: 'Clear guidance. Responsible technology. Designed for real-world health decisions.',
    trustLead:
      'DEDAN is an AI-assisted navigation tool. It helps you understand urgency and decide what to do next — it does not diagnose and does not replace a clinician.',
    trustP1Title: 'Your data stays yours',
    trustP1Body:
      'Assessment data is used to produce your guidance. You decide what to share, and you can withdraw consent at any time.',
    trustP2Title: 'AI-assisted, not autonomous',
    trustP2Body:
      'Every result is generated from the information you provide and labelled as AI-generated. No hidden reasoning is shown or implied.',
    trustP3Title: 'Guideline-supported',
    trustP3Body:
      'Urgency levels are mapped to recognised clinical guidance references, which are listed with each result.',
    trustP4Title: 'You stay in control',
    trustP4Body:
      'You can review your history, request a fresh assessment, or seek in-person care at any point.',

    howEyebrow: 'How DEDAN works',
    howTitle: 'Four steps from symptom to next step.',
    howLead:
      'The assessment is deliberately short. Each step builds on the last, so you are never asked to understand clinical concepts you were not given.',
    step1Title: "Tell us what you're experiencing",
    step1Body:
      'Describe your symptoms in your own words, then confirm the details DEDAN asks about.',
    step2Title: 'Add the context that matters',
    step2Body:
      'Age, sex, pregnancy status and existing conditions change how symptoms should be interpreted.',
    step3Title: 'DEDAN evaluates the information',
    step3Body:
      'Your responses are assessed against clinical guidance to determine an urgency level.',
    step4Title: 'Review your guidance and next steps',
    step4Body:
      'You receive a clear recommended action, what to monitor, and when to seek urgent help.',

    capsEyebrow: 'What DEDAN covers',
    capsTitle: 'Support for the decisions people actually face.',
    capsLead:
      'DEDAN focuses on the common, high-volume questions where clear guidance changes what someone does next.',
    cap1Title: 'Symptom assessment',
    cap1Body:
      'Fever, cough, chest pain, abdominal pain, headache, injury and more — assessed for urgency.',
    cap2Title: 'Urgency guidance',
    cap2Body:
      'A single, unambiguous urgency level: emergency, urgent, routine, or self-care.',
    cap3Title: 'Next-step guidance',
    cap3Body:
      'What to do now, what to monitor, and the specific signs that mean you should escalate.',
    cap4Title: 'Condition context',
    cap4Body:
      'Plain-language explanation of the conditions the backend actually returns for your assessment.',

    continuityEyebrow: 'Continuity',
    continuityTitle: 'Guidance you can come back to.',
    continuityLead:
      'Health decisions rarely end with one conversation. DEDAN keeps a local record of your assessments so you can return to what you were advised, and recognise when something changes.',

    aiEyebrow: 'Responsible AI',
    aiTitle: 'Built to be trustworthy before it is impressive.',
    aiLead:
      'Healthcare AI earns trust through restraint: clear boundaries, visible limits, and no invented clinical authority.',
    ai1Title: 'Clear boundaries',
    ai1Body:
      'DEDAN provides guidance, not diagnosis. Emergency results direct you to human care immediately.',
    ai2Title: 'Visible limits',
    ai2Body:
      'Results state what was assessed and what was not. Uncertainty is stated rather than hidden.',
    ai3Title: 'No hidden reasoning',
    ai3Body:
      'You only see the summary, the urgency level and the cited guidance — never fabricated clinical reasoning.',
    ai4Title: 'Human care first',
    ai4Body:
      'Every result ends with explicit escalation instructions for when professional care is needed.',

    finalTitle: 'Ready to understand what you are experiencing?',
    finalLead:
      'An assessment takes a few minutes. You can stop at any point, and nothing is shared without your consent.',
    finalSecondary: 'Read how it works',
  },
  /** Assessment shell (master spec 8): guided, calm, progressive disclosure. */
  assess: {
    step: 'Step {current} of {total}',
    step1Title: "Let's start with a few basics.",
    step1Lead:
      'These details change how symptoms should be interpreted. Nothing here is shared without your consent.',
    step2Title: "Let's understand what you're experiencing.",
    step2Lead:
      'Describe your symptoms in your own words. You can add detail as DEDAN asks for it.',
    ageHelp: 'Used to interpret symptoms across different age groups.',
    sexHelp: 'Some symptoms carry different risk depending on sex.',
    locationHelp: 'Optional. Used only to show locally relevant guidance.',
    chronicHelp: 'Select any long-term conditions you are managing. Optional.',
    languageHelp: 'Only languages with a complete translation are selectable.',
    back: 'Back',
    continue: 'Continue',
    toSymptoms: 'Continue to symptoms',
    reviewNotice: 'You can review or change anything before your assessment is sent.',

    /* --- Step 2: symptoms --- */
    symptomsLabel: 'Describe your symptoms',
    symptomsHelp:
      'Include what you feel, where it is, how long it has lasted, and anything that makes it better or worse.',
    symptomsPlaceholder: 'For example: sharp chest pain spreading to my left arm for about 2 hours, worse when I breathe in.',
    symptomsTooShort: 'Please describe your symptoms in at least a few words (5 characters minimum).',
    durationLabel: 'How long have you had this?',
    durationHelp: 'An approximate answer is fine.',
    severityLabel: 'How severe does it feel right now?',
    severityHelp: 'Your own description is what matters — there is no wrong answer.',
    severityMild: 'Mild — noticeable but I can continue normally',
    severityModerate: 'Moderate — it is affecting what I can do',
    severitySevere: 'Severe — I cannot continue normally',
    durationHours: 'Less than 24 hours',
    durationDays: 'A few days (2–7)',
    durationWeeks: 'One to four weeks',
    durationMonths: 'More than a month',
    durationUnknown: 'Not sure',
    processingTitle: 'Preparing your guidance',
    processingNote: 'DEDAN is sending your information for assessment. Keep this page open — this usually takes a few seconds.',
    submit: 'Get my guidance',
    submitting: 'Sending…',
  },
  profile: {
    title: 'Your Information',
    age: 'Age',
    sex: 'Sex',
    male: 'Male',
    female: 'Female',
    other: 'Other',
    location: 'Location (city/region)',
    pregnancy: 'Pregnant or recently pregnant (within 6 weeks)',
    chronic: 'Chronic conditions (select all that apply)',
    language: 'Preferred language',
    none: 'None',
    submit: 'Continue to Assessment',
            ageError: 'Please enter a valid age (0–120).',
    sexError: 'Please select a sex.',
    privacy: 'Your information is confidential and used only to provide triage. Data is anonymized for system improvement.',
  },
  symptoms: {
    title: 'Describe your symptoms',
    placeholder: 'E.g. sharp chest pain radiating to my left arm for 2 hours',
    duration: 'Duration',
    severity: 'Severity',
    mild: 'Mild',
    moderate: 'Moderate',
    severe: 'Severe',
    send: 'Continue',
  },
  triage: {
    intro: 'DEDAN will review your information against clinical guidance.',
    reviewing: 'Reviewing your information',
    checking: 'Checking relevant guidance',
    deciding: 'Preparing your next-step recommendation',
    error: 'We could not complete the assessment. Your information was not lost — please try again.',
    retry: 'Try again',
    offline: 'You are offline. The assessment will be sent when you reconnect.',
  },
  results: {
    emergency: 'Urgent Action Required',
    urgent: 'Prompt Medical Attention',
    routine: 'Next Step',
    selfCare: 'Self-Care Guidance',
    confidence: 'Confidence',
    nextStep: 'Recommended next step',
    summary: 'Assessment summary',
    whenToSeek: 'When to seek emergency care',
    share: 'Share report',
    newAssessment: 'New assessment',

    /* --- Structured result presentation (master spec 9 / 16 / 17) --- */
    yourGuidance: 'Your guidance',
    providedByYou: 'Based on the information you provided',
    generatedByAi: 'AI-generated assessment',
    whatToDoNow: 'What to do now',
    whatWeNoticed: 'What DEDAN noticed',
    riskFlagsEmpty: 'No specific risk indicators were identified from your responses.',
    followUpLabel: 'Suggested follow-up',
    whenToSeekEmergencyBody:
      'Seek emergency care immediately if your symptoms become severe, you have difficulty breathing, chest pain, confusion, fainting, heavy bleeding, or you feel your life is in danger. Do not wait for another assessment.',
    uncertainty:
      'This guidance is based only on the information you provided. It cannot rule out a serious condition. If you are worried, seek professional medical care.',
    callEmergency: 'Call emergency number',
    viewHistory: 'View assessment history',
    noResultsTitle: 'No assessment to show',
    noResultsBody:
      'Results are shown immediately after an assessment. Your previous assessments are always available in your history.',
    startAssessment: 'Start an assessment',
    offlineNotice: 'Your assessment was not sent. Nothing was lost — retry when your connection returns.',
    confidenceNote: 'A measure of how confident the assessment was, not a diagnosis.',
  },
  history: {
    title: 'Your Assessments',
    empty: 'No assessments yet',
    emptyDesc: 'Start your first health assessment to see your history here.',
    lastUpdated: 'Updated',
  },
  followUp: {
    title: 'Follow-Up',
    empty: 'No follow-ups scheduled',
    emptyDesc: 'Scheduled check-ins and reminders will appear here.',
  },
  help: {
    title: 'Help & FAQ',
    privacy: 'Privacy',
    consent: 'Data consent',
    noQuestions: 'No questions available offline.',
  },
  pricing: {
    title: 'Pricing',
    comingSoon: 'Pricing is coming soon',
    desc: 'Subscription options will be available in your region soon. You will always have access to basic triage.',
  },
  errors: {
    offlineTitle: 'You are offline',
    offlineDesc: 'Check your connection and retry.',
    genericTitle: 'Something went wrong',
    retry: 'Retry',
    backHome: 'Back to home',
  },
} as const;

export type Messages = typeof en;
export type MessageKey = keyof typeof en;
