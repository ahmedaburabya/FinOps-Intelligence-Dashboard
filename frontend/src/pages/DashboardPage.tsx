// frontend/src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableContainer,
  Paper,
} from '@mui/material';
import { finopsApi } from '../services';
import { useFinopsOverview, useAggregatedCostData } from '../hooks/useFinopsData';
import LoadingSpinner from '../components/common/LoadingSpinner';
import SnackbarAlert from '../components/common/SnackbarAlert';
import type { AggregatedCostData, FinopsOverview, LLMInsight } from '../types/finops';

const DashboardPage: React.FC = () => {
  const [projectFilter, setProjectFilter] = useState<string>('');
  const [serviceFilter, setServiceFilter] = useState<string>('');
  const [skuFilter, setSkuFilter] = useState<string>('');
  const [startDateFilter, setStartDateFilter] = useState<string>('');
  const [endDateFilter, setEndDateFilter] = useState<string>('');

  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, setItemsPerPage] = useState<number>(10);
  const [totalItems, setTotalItems] = useState<number>(0); // This would ideally come from the backend

  const {
    overview,
    loading: overviewLoading,
    error: overviewError,
    refetchOverview,
  } = useFinopsOverview(projectFilter || undefined);

  const {
    costData,
    loading: costDataLoading,
    error: costDataError,
    refetchCostData,
  } = useAggregatedCostData({
    skip: (currentPage - 1) * itemsPerPage,
    limit: itemsPerPage,
    service: serviceFilter || undefined,
    project: projectFilter || undefined,
    sku: skuFilter || undefined,
    start_date: startDateFilter ? new Date(startDateFilter).toISOString() : undefined,
    end_date: endDateFilter ? new Date(endDateFilter).toISOString() : undefined,
  });

  const [llmSummaryLoading, setLlmSummaryLoading] = useState<boolean>(false);
  const [llmSummaryError, setLlmSummaryError] = useState<string | null>(null);
  const [llmInsight, setLlmInsight] = useState<LLMInsight | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');

  const handleApplyFilters = () => {
    setCurrentPage(1); // Reset to first page on new filter
    refetchCostData();
    refetchOverview();
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setCurrentPage(value);
    // refetchCostData is already dependent on currentPage, so it will re-fetch
  };

  const generateSummary = async () => {
    setLlmSummaryLoading(true);
    setLlmSummaryError(null);
    setLlmInsight(null);
    try {
      const summary = await finopsApi.generateSpendSummary({
        project: projectFilter || undefined,
        start_date: startDateFilter ? new Date(startDateFilter).toISOString() : undefined,
        end_date: endDateFilter ? new Date(endDateFilter).toISOString() : undefined,
      });
      setLlmInsight(summary);
      setSnackbarMessage('AI spend summary generated successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (err: any) {
      console.error('Failed to generate LLM summary:', err);
      setLlmSummaryError(err.response?.data?.detail || 'Failed to generate AI spend summary.');
      setSnackbarMessage(err.response?.data?.detail || 'Failed to generate AI spend summary.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLlmSummaryLoading(false);
    }
  };

  const handleSnackbarClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  // Mock totalItems for pagination since backend doesn't provide it yet
  useEffect(() => {
    if (costData && !costDataLoading) {
        // This is a crude way to estimate total pages if no total count is provided by API
        // In a real app, API would return total_count
        if (costData.length < itemsPerPage && currentPage === 1) {
            setTotalItems(costData.length);
        } else if (costData.length === itemsPerPage) {
            setTotalItems(currentPage * itemsPerPage + 1); // Assume more if full page
        }
    }
  }, [costData, costDataLoading, itemsPerPage, currentPage]);


  if (overviewLoading && costDataLoading) {
    return <LoadingSpinner message="Loading FinOps Dashboard..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        FinOps Intelligence Dashboard
      </Typography>

      <SnackbarAlert
        open={snackbarOpen}
        message={snackbarMessage}
        severity={snackbarSeverity}
        onClose={handleSnackbarClose}
      />

      {(overviewError || costDataError || llmSummaryError) && (
        <SnackbarAlert
          open={true} // Always open if there's an error
          message={overviewError?.detail || costDataError?.detail || llmSummaryError || 'An unknown error occurred.'}
          severity="error"
          onClose={() => {
              overviewError ? refetchOverview() : null;
              costDataError ? refetchCostData() : null;
              llmSummaryError ? setLlmSummaryError(null) : null;
          }}
          autoHideDuration={null} // Keep open until user dismisses or issue is resolved
        />
      )}

      {/* FinOps Overview Cards */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Financial Overview
        </Typography>
        {overviewLoading ? (
          <CircularProgress />
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card raised>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Month-to-Date Spend
                  </Typography>
                  <Typography variant="h5" component="div">
                    {overview?.mtd_spend !== undefined ? `$${overview.mtd_spend.toFixed(2)}` : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card raised>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Estimated Monthly Burn Rate
                  </Typography>
                  <Typography variant="h5" component="div">
                    {overview?.burn_rate_estimated_monthly !== undefined ? `$${overview.burn_rate_estimated_monthly.toFixed(2)}` : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            {/* Add more overview cards here if needed */}
          </Grid>
        )}
      </Box>

      {/* Filters for Aggregated Cost Data */}
      <Box sx={{ my: 4, p: 3, border: '1px solid #e0e0e0', borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filter Aggregated Cost Data
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Project ID"
              variant="outlined"
              fullWidth
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Service"
              variant="outlined"
              fullWidth
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="SKU"
              variant="outlined"
              fullWidth
              value={skuFilter}
              onChange={(e) => setSkuFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Start Date"
              type="date"
              variant="outlined"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={startDateFilter}
              onChange={(e) => setStartDateFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="End Date"
              type="date"
              variant="outlined"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={endDateFilter}
              onChange={(e) => setEndDateFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button variant="contained" onClick={handleApplyFilters} fullWidth>
              Apply Filters
            </Button>
          </Grid>
        </Grid>
      </Box>

      {/* Aggregated Cost Data Table */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Aggregated Cost Data
        </Typography>
        {costDataLoading ? (
          <LoadingSpinner message="Loading cost data..." />
        ) : (
          <>
            <TableContainer component={Paper}>
              <Table sx={{ minWidth: 650 }} aria-label="aggregated cost data table">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Service</TableCell>
                    <TableCell>Project</TableCell>
                    <TableCell>SKU</TableCell>
                    <TableCell align="right">Cost (USD)</TableCell>
                    <TableCell align="right">Usage Amount</TableCell>
                    <TableCell>Time Period</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {costData.length > 0 ? (
                    costData.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell component="th" scope="row">
                          {row.id}
                        </TableCell>
                        <TableCell>{row.service}</TableCell>
                        <TableCell>{row.project || 'N/A'}</TableCell>
                        <TableCell>{row.sku}</TableCell>
                        <TableCell align="right">{row.cost.toFixed(2)}</TableCell>
                        <TableCell align="right">{row.usage_amount?.toFixed(2) || 'N/A'} {row.usage_unit || ''}</TableCell>
                        <TableCell>{new Date(row.time_period).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        No aggregated cost data found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Pagination
                count={Math.ceil(totalItems / itemsPerPage)}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          </>
        )}
      </Box>

      {/* LLM Insight Panel */}
      <Box sx={{ my: 4, p: 3, border: '1px solid #e0e0e0', borderRadius: 2 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          AI-Driven Insights
        </Typography>
        <Button
          variant="contained"
          onClick={generateSummary}
          disabled={llmSummaryLoading}
          sx={{ mb: 2 }}
        >
          {llmSummaryLoading ? <CircularProgress size={24} /> : 'Generate Spend Summary'}
        </Button>
        {llmInsight && (
          <Card variant="outlined" sx={{ mt: 2, backgroundColor: '#f5f5f5' }}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                AI Spend Summary ({llmInsight.insight_type})
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                {llmInsight.insight_text}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Generated on: {new Date(llmInsight.timestamp).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>
    </Container>
  );
};

export default DashboardPage;
