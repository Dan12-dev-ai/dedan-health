import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Alert,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  LocalHospital as HospitalIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { TriageCase, ClinicStats } from '../types';
import { clinicAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<ClinicStats | null>(null);
  const [recentCases, setRecentCases] = useState<TriageCase[]>([]);
  const [emergencyAlerts, setEmergencyAlerts] = useState<TriageCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsData, casesData, alertsData] = await Promise.all([
        clinicAPI.getStats(),
        clinicAPI.getTriageCases({ limit: 10, status: 'pending' }),
        clinicAPI.getEmergencyAlerts(),
      ]);

      setStats(statsData);
      setRecentCases(casesData.cases || []);
      setEmergencyAlerts(alertsData.alerts || []);
      setError(null);
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    loadDashboardData();
  };

  const getTriageLevelColor = (level: string) => {
    switch (level) {
      case 'emergency': return '#d32f2f';
      case 'urgent': return '#f57c00';
      case 'routine': return '#1976d2';
      case 'self_care': return '#388e3c';
      default: return '#666666';
    }
  };

  const getTriageLevelIcon = (level: string) => {
    switch (level) {
      case 'emergency': return '🔴';
      case 'urgent': return '🟡';
      case 'routine': return '🟢';
      case 'self_care': return '🔵';
      default: return '⚪';
    }
  };

  const pieColors = ['#d32f2f', '#f57c00', '#1976d2', '#388e3c'];

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading dashboard...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={handleRefresh} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Clinic Console powered by DEDAN
        </Typography>
        <Button variant="outlined" onClick={handleRefresh} startIcon={<RefreshIcon />}>
          Refresh
        </Button>
      </Box>

      {/* Emergency Alerts */}
      {emergencyAlerts.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <WarningIcon sx={{ mr: 1 }} />
            <Typography variant="h6">
              {emergencyAlerts.length} Emergency Case{emergencyAlerts.length > 1 ? 's' : ''} Require Immediate Attention
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <PeopleIcon sx={{ fontSize: 40, color: '#1976d2', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="primary">
                    {stats?.total_cases || 0}
                  </Typography>
                  <Typography color="textSecondary">Total Cases</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <WarningIcon sx={{ fontSize: 40, color: '#d32f2f', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="error">
                    {stats?.cases_by_level?.emergency || 0}
                  </Typography>
                  <Typography color="textSecondary">Emergency Cases</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUpIcon sx={{ fontSize: 40, color: '#f57c00', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="warning.main">
                    {stats?.cases_by_level?.urgent || 0}
                  </Typography>
                  <Typography color="textSecondary">Urgent Cases</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AssessmentIcon sx={{ fontSize: 40, color: '#388e3c', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="success.main">
                    {Math.round((stats?.accuracy_metrics?.dedan_vs_doctor_agreement || 0) * 100)}%
                  </Typography>
                  <Typography color="textSecondary">Accuracy Rate</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Cases by Triage Level */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cases by Triage Level
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Emergency', value: stats?.cases_by_level?.emergency || 0 },
                      { name: 'Urgent', value: stats?.cases_by_level?.urgent || 0 },
                      { name: 'Routine', value: stats?.cases_by_level?.routine || 0 },
                      { name: 'Self Care', value: stats?.cases_by_level?.self_care || 0 },
                    ]}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {[
                      { name: 'Emergency', value: stats?.cases_by_level?.emergency || 0 },
                      { name: 'Urgent', value: stats?.cases_by_level?.urgent || 0 },
                      { name: 'Routine', value: stats?.cases_by_level?.routine || 0 },
                      { name: 'Self Care', value: stats?.cases_by_level?.self_care || 0 },
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Cases Over Time */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cases Over Time (Last 7 Days)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats?.cases_by_day || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="cases" stroke="#1976d2" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Cases */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Recent Triage Cases
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => window.location.href = '/cases'}
              >
                View All Cases
              </Button>
            </Box>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Case ID</TableCell>
                    <TableCell>Time</TableCell>
                    <TableCell>Patient Info</TableCell>
                    <TableCell>DEDAN Assessment</TableCell>
                    <TableCell>Doctor Review</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentCases.map((caseItem) => (
                    <TableRow key={caseItem.id}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {caseItem.id.slice(-8)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {new Date(caseItem.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">
                            Age: {caseItem.patient_info.age_group}
                          </Typography>
                          <Typography variant="body2">
                            Sex: {caseItem.patient_info.sex}
                          </Typography>
                          <Typography variant="body2">
                            Lang: {caseItem.patient_info.language}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography>
                            {getTriageLevelIcon(caseItem.dedan_assessment.triage_level)}
                          </Typography>
                          <Chip
                            label={caseItem.dedan_assessment.triage_level.toUpperCase()}
                            size="small"
                            sx={{
                              backgroundColor: getTriageLevelColor(caseItem.dedan_assessment.triage_level),
                              color: 'white',
                            }}
                          />
                          <Typography variant="caption">
                            {Math.round(caseItem.dedan_assessment.confidence_score * 100)}% confident
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {caseItem.clinic_review.status === 'pending' ? (
                          <Chip label="Pending Review" color="warning" size="small" />
                        ) : (
                          <Box>
                            <Typography variant="body2">
                              {caseItem.clinic_review.final_triage_level?.toUpperCase() || 'N/A'}
                            </Typography>
                            <Typography variant="caption">
                              by {caseItem.clinic_review.reviewed_by || 'Unknown'}
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View Case Details">
                          <IconButton
                            size="small"
                            onClick={() => window.location.href = `/cases/${caseItem.id}`}
                          >
                            <HospitalIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Box>
  );
};

export default Dashboard;
