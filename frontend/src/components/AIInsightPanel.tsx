// frontend/src/components/AIInsightPanel.tsx
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Typography,
  Paper,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { finopsApi } from '~/services';
import { AIInsightRequest } from '~/types/finops';
import SnackbarAlert from './common/SnackbarAlert'; // Assuming SnackbarAlert is in common

interface AIInsightPanelProps {
  // Filters from the main dashboard to provide context to the AI
  currentProjectFilter?: string;
  currentServiceFilter?: string;
  currentSkuFilter?: string;
  currentStartDateFilter?: string;
  currentEndDateFilter?: string;
}

const AIInsightPanel: React.FC<AIInsightPanelProps> = ({
  currentProjectFilter,
  currentServiceFilter,
  currentSkuFilter,
  currentStartDateFilter,
  currentEndDateFilter,
}) => {
  const [userQuery, setUserQuery] = useState<string>('');
  const [insightType, setInsightType] = useState<AIInsightRequest['insight_type']>('natural_query');
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const { mutate: getInsight, isPending: isLoading, error } = useMutation({
    mutationFn: (request: AIInsightRequest) => finopsApi.getAIInsight(request),
    onSuccess: (data) => {
      setAiResponse(data);
      setSnackbarMessage('AI insight generated successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    },
    onError: (err) => {
      console.error('Failed to get AI insight:', err);
      setAiResponse(`Error: ${err.message}`);
      setSnackbarMessage(`Failed to get AI insight: ${err.message}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    },
  });

  const handleGenerateInsight = () => {
    if (!userQuery && insightType === 'natural_query') {
      setSnackbarMessage('Please enter a query for natural language insights.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }

    const requestBody: AIInsightRequest = {
      query: userQuery || undefined,
      insight_type: insightType,
      project: currentProjectFilter || undefined,
      service: currentServiceFilter || undefined,
      sku: currentSkuFilter || undefined,
      start_date: currentStartDateFilter || undefined,
      end_date: currentEndDateFilter || undefined,
    };
    getInsight(requestBody);
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  return (
    <Box sx={{ p: 3, border: '1px solid #e0e0e0', borderRadius: 2, mt: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        AI-Powered FinOps Insights
      </Typography>

      <SnackbarAlert
        open={snackbarOpen}
        message={snackbarMessage}
        severity={snackbarSeverity}
        onClose={handleSnackbarClose}
      />

      <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
        <InputLabel id="insight-type-label">Insight Type</InputLabel>
        <Select
          labelId="insight-type-label"
          id="insight-type-select"
          value={insightType}
          label="Insight Type"
          onChange={(e) => setInsightType(e.target.value as AIInsightRequest['insight_type'])}
        >
          <MenuItem value="natural_query">Natural Language Query</MenuItem>
          <MenuItem value="summary">Spend Summary</MenuItem>
          <MenuItem value="anomaly">Anomaly Detection</MenuItem>
          <MenuItem value="prediction">Predictive Forecasting</MenuItem>
          <MenuItem value="recommendation">Recommendations</MenuItem>
        </Select>
      </FormControl>

      {(insightType === 'natural_query' || insightType === 'root_cause') && (
        <TextField
          label="Your Question to AI"
          variant="outlined"
          fullWidth
          multiline
          rows={2}
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          sx={{ mb: 2 }}
          placeholder="e.g., Why did my BigQuery costs increase last month?"
        />
      )}

      <Button
        variant="contained"
        onClick={handleGenerateInsight}
        disabled={isLoading}
        fullWidth
        sx={{ mb: 2 }}
      >
        {isLoading ? <CircularProgress size={24} /> : 'Generate AI Insight'}
      </Button>

      {aiResponse && (
        <Paper elevation={1} sx={{ p: 2, backgroundColor: '#f5f5f5', whiteSpace: 'pre-line' }}>
          <Typography variant="h6" gutterBottom>
            AI Response:
          </Typography>
          <Typography variant="body1">{aiResponse}</Typography>
        </Paper>
      )}
    </Box>
  );
};

export default AIInsightPanel;
