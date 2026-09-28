import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Dashboard from './pages/Dashboard';
import CaseManagement from './pages/CaseManagement';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

// DEDAN Clinic Console theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Medical blue
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#ffffff', // Clean white
    },
    error: {
      main: '#d32f2f', // Emergency red
    },
    warning: {
      main: '#f57c00', // Urgent orange
    },
    success: {
      main: '#388e3c', // Self-care green
    },
    info: {
      main: '#1976d2', // Routine blue
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
      color: '#1976d2',
    },
    h6: {
      fontWeight: 500,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cases" element={<CaseManagement />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;
