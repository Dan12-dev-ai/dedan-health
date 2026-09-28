/**
 * DEDAN-Health - Patient Application Shell (re-architected)
 *
 * Premium-bright global healthcare intelligence interface.
 * Patient navigation (master spec 52): Home | Assess | History | Follow-Up | Help
 * Secondary: Profile, Settings, Consent, Pricing.
 *
 * Wired ONLY to the live v1 backend routes (backend/main.py). Pricing/billing
 * and the clinician workspace are architecturally separated (master spec 59:
 * "Do not merge the two frontends") and marked unavailable - never faked.
 */
import React from 'react';
import {
  CssBaseline,
  Box,
} from '@mui/material';
import {
  BrowserRouter as Router, Routes, Route, Navigate,
} from 'react-router-dom';
import { DedanThemeProvider } from './design-system/theme';
import { DedanStateProvider } from './state/DedanContext';
import { Header } from './layout/Header';
import { Footer } from './layout/Footer';
import { NetworkBanner } from './components/NetworkBanner';
import {
  HomePage, AssessPage, TriagePage, ResultsPage, HistoryPage,
  SessionDetailPage, FollowUpPage, HelpPage, ConsentPage,
  SettingsPage, PricingPage,
} from './pages';

function RootRedirect() {
  return <Navigate to="/" replace />;
}

const AppLayout: React.FC = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <NetworkBanner />

      <Box component="main" sx={{ flex: 1, width: '100%' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/assess" element={<AssessPage />} />
          <Route path="/profile" element={<AssessPage />} />
          <Route path="/triage" element={<TriagePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:sessionId" element={<SessionDetailPage />} />
          <Route path="/follow-up" element={<FollowUpPage />} />
          <Route path="/help" element={<HelpPage />} />
          <Route path="/consent" element={<ConsentPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="*" element={<RootRedirect />} />
        </Routes>
      </Box>

      <Footer />
    </Box>
);

const App: React.FC = () => (
  <DedanThemeProvider>
    <DedanStateProvider>
      <CssBaseline />
      <Router>
        <AppLayout />
      </Router>
    </DedanStateProvider>
  </DedanThemeProvider>
);

export default App;
