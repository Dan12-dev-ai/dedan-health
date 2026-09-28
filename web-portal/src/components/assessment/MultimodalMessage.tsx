/**
 * MultimodalMessage — Displays AI response with safety-first rendering.
 *
 * Emergency/urgent states are visually prioritized.
 * No clinical decisions are made in the frontend.
 */

import React from 'react';
import {
  Box, Typography, Alert, Chip, List, ListItem, ListItemText, Divider,
} from '@mui/material';
import { Warning, Info } from '@mui/icons-material';
import { radius } from '../../design-system/tokens';
import type { MultimodalAnalyzeResponse } from './types';

export interface MultimodalMessageProps {
  response?: MultimodalAnalyzeResponse;
  loading?: boolean;
}

const urgencyConfig = {
  emergency: { color: 'error' as const, icon: <Warning />, label: 'EMERGENCY' },
  urgent: { color: 'warning' as const, icon: <Warning />, label: 'URGENT' },
  routine: { color: 'info' as const, icon: <Info />, label: 'ROUTINE' },
  self_care: { color: 'success' as const, icon: <Info />, label: 'SELF CARE' },
};

export const MultimodalMessage: React.FC<MultimodalMessageProps> = ({ response, loading }) => {
  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">Analyzing your symptoms...</Typography>
      </Box>
    );
  }

  if (!response) return null;

  const urgency = urgencyConfig[response.urgency];

  return (
    <Box sx={{ width: '100%' }}>
      {/* Urgency banner - highest priority */}
      <Alert
        severity={urgency.color}
        icon={urgency.icon}
        sx={{ mb: 2, borderRadius: radius.lg }}
        action={
          <Chip
            label={urgency.label}
            size="small"
            color={urgency.color}
            sx={{ ml: 1 }}
          />
        }
      >
        <Typography sx={{ fontWeight: 600 }}>{response.recommended_next_step}</Typography>
      </Alert>

      {/* Safety notice for emergency/urgent */}
      {(response.urgency === 'emergency' || response.urgency === 'urgent') && (
        <Alert severity="error" sx={{ mb: 2, borderRadius: radius.lg }}>
          <Typography sx={{ fontWeight: 600 }}>Safety Notice</Typography>
          <Typography>{response.safety_notice}</Typography>
        </Alert>
      )}

      {/* Professional review requirement */}
      {response.requires_professional_review && (
        <Alert severity="warning" sx={{ mb: 2, borderRadius: radius.lg }}>
          <Typography sx={{ fontWeight: 600 }}>Professional Review Required</Typography>
          <Typography>This assessment requires review by a healthcare professional.</Typography>
        </Alert>
      )}

      {/* Image assessment */}
      {response.image_assessment && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Image Analysis</Typography>
          {response.image_assessment.observations.length > 0 && (
            <List dense>
              {response.image_assessment.observations.map((obs, i) => (
                <ListItem key={i}><ListItemText primary={obs} /></ListItem>
              ))}
            </List>
          )}
          {response.image_assessment.limitations.length > 0 && (
            <Typography variant="caption" color="text.secondary">
              Limitations: {response.image_assessment.limitations.join('; ')}
            </Typography>
          )}
        </Box>
      )}

      {/* Medical information */}
      {response.medical_information.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Medical Information</Typography>
          {response.medical_information.map((info, i) => (
            <Box key={i} sx={{ mb: 1, p: 1, borderRadius: radius.sm, backgroundColor: 'background.paper' }}>
              <Typography variant="body2"><strong>{info.topic}</strong></Typography>
              <Typography variant="body2" color="text.secondary">{info.content}</Typography>
              <Typography variant="caption" color="text.secondary">Source: {info.source}</Typography>
            </Box>
          ))}
        </Box>
      )}

      {/* Warning signs */}
      {response.warning_signs.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2, borderRadius: radius.lg }}>
          <Typography sx={{ fontWeight: 600 }}>Warning Signs</Typography>
          <List dense>
            {response.warning_signs.map((sign, i) => (
              <ListItem key={i}><ListItemText primary={sign} /></ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Follow-up questions */}
      {response.follow_up_questions.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Follow-up Questions</Typography>
          {response.follow_up_questions.map((q, i) => (
            <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>• {q}</Typography>
          ))}
        </Box>
      )}

      {/* Sources */}
      {response.sources.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Sources: {response.sources.map(s => s.title).join(', ')}
          </Typography>
        </Box>
      )}

      {/* Uncertainty */}
      {response.uncertainty && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Uncertainty: {response.uncertainty}
        </Typography>
      )}

      {/* Confidence */}
      <Typography variant="caption" color="text.secondary">
        Confidence: {Math.round(response.confidence_score * 100)}% | Provider: {response.provider} | Model: {response.model}
      </Typography>
    </Box>
  );
};

export default MultimodalMessage;