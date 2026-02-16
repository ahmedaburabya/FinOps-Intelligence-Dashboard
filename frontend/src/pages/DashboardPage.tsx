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
  Pagination,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableContainer,
  Paper,
  FormControl, // Added for Select
  InputLabel, // Added for Select
  Select, // Added for Select
  MenuItem, // Added for Select
} from '@mui/material';

import { finopsApi } from '~/services';
import {
  useFinopsOverview,
  useAggregatedCostData,
  useDistinctServices,
  useDistinctProjects,
  useDistinctSkus,
} from '~/hooks/useFinopsData'; // Added useDistinctServices, useDistinctProjects, useDistinctSkus
import LoadingSpinner from '~/components/common/LoadingSpinner';
import SnackbarAlert from '~/components/common/SnackbarAlert';
import { AxiosError } from 'axios';
import type { AggregatedCostData, FinopsOverview, LLMInsight } from '~/types/finops'; // Using import type
import AIInsightPanel from '~/components/AIInsightPanel'; // Import the new AIInsightPanel component

const DashboardPage: React.FC = () => {
  const [projectFilter, setProjectFilter] = useState<string>('');
  const [serviceFilter, setServiceFilter] = useState<string>('');
  const [skuFilter, setSkuFilter] = useState<string>('');
  const [startDateFilter, setStartDateFilter] = useState<string>('');
  const [endDateFilter, setEndDateFilter] = useState<string>('');

  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, _setItemsPerPage] = useState<number>(10); // Renamed to silence unused error
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

  const {
    distinctServices,
    loading: distinctServicesLoading,
    error: distinctServicesError,
  } = useDistinctServices(); // Fetch distinct services

  const {
    distinctProjects,
    loading: distinctProjectsLoading,
    error: distinctProjectsError,
  } = useDistinctProjects(); // Fetch distinct projects

  const {
    distinctSkus,
    loading: distinctSkusLoading,
    error: distinctSkusError,
  } = useDistinctSkus(); // Fetch distinct SKUs

  const [llmSummaryLoading, setLlmSummaryLoading] = useState<boolean>(false);
  const [llmSummaryError, setLlmSummaryError] = useState<string | null>(null);
  const [llmInsight, setLlmInsight] = useState<LLMInsight | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<
    'success' | 'error' | 'info' | 'warning'
  >('success');

  const handleApplyFilters = () => {
    setCurrentPage(1); // Reset to first page on new filter
    refetchCostData();
    refetchOverview();
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    // Prefixed with _
    setCurrentPage(value);
    // refetchCostData is already dependent on currentPage, so it will re-fetch
  };

  const generateSummary = async () => {
    setLlmSummaryLoading(true);
    setLlmSummaryError(null);
    setLlmInsight(null);
    try {
      const summary = await finopsApi.generateSpendSummary({
        service: serviceFilter || undefined,
        project: projectFilter || undefined,
        sku: skuFilter || undefined,
        start_date: startDateFilter ? new Date(startDateFilter).toISOString() : undefined,
        end_date: endDateFilter ? new Date(endDateFilter).toISOString() : undefined,
      });
      setLlmInsight(summary);
      setSnackbarMessage('AI spend summary generated successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (err: unknown) {
      console.error('Failed to generate LLM summary:', err);
      const axiosError = err as AxiosError<{ detail?: string }>;
      setLlmSummaryError(
        axiosError.response?.data?.detail || 'Failed to generate AI spend summary.',
      );
      setSnackbarMessage(
        axiosError.response?.data?.detail || 'Failed to generate AI spend summary.',
      );
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLlmSummaryLoading(false);
    }
  };

  const handleSnackbarClose = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    // Prefixed with _
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

  if (
    overviewLoading &&
    costDataLoading &&
    distinctServicesLoading &&
    distinctProjectsLoading &&
    distinctSkusLoading
  ) {
    // Added distinctProjectsLoading and distinctSkusLoading
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

      {(overviewError ||
        costDataError ||
        llmSummaryError ||
        distinctServicesError ||
        distinctProjectsError ||
        distinctSkusError) && ( // Added distinctProjectsError and distinctSkusError
        <SnackbarAlert
          open={true} // Always open if there's an error
          message={
            overviewError?.detail ||
            costDataError?.detail ||
            llmSummaryError ||
            distinctServicesError?.message || // Display distinctServicesError message
            distinctProjectsError?.message || // Display distinctProjectsError message
            distinctSkusError?.message || // Display distinctSkusError message
            'An unknown error occurred.'
          }
          severity="error"
          onClose={() => {
            overviewError ? refetchOverview() : null;
            costDataError ? refetchCostData() : null;
            llmSummaryError ? setLlmSummaryError(null) : null;
            distinctServicesError ? (distinctServicesError.message = null) : null; // Clear distinctServicesError
            distinctProjectsError ? (distinctProjectsError.message = null) : null; // Clear distinctProjectsError
            distinctSkusError ? (distinctSkusError.message = null) : null; // Clear distinctSkusError
          }}
          autoHideDuration={undefined} // Changed from null to undefined
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
            <Grid item xs={12} sm={6} md={3} component="div">
              <Card raised>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Month-to-Date Spend
                  </Typography>
                  <Typography variant="h5">
                    {overview?.mtd_spend !== undefined
                      ? `$${overview.mtd_spend.toFixed(2)}`
                      : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3} component="div">
              <Card raised>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Estimated Monthly Burn Rate
                  </Typography>
                  <Typography variant="h5">
                    {overview?.burn_rate_estimated_monthly !== undefined
                      ? `$${overview.burn_rate_estimated_monthly.toFixed(2)}`
                      : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            {/* New card for Daily Burn Rate MTD */}
            <Grid item xs={12} sm={6} md={3} component="div">
              <Card raised>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Daily Burn Rate (average)
                  </Typography>
                  <Typography variant="h5">
                    {overview?.daily_burn_rate_mtd !== undefined
                      ? `$${overview.daily_burn_rate_mtd.toFixed(2)}`
                      : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            {/* New card for Projected Month-End Spend */}
            <Grid item xs={12} sm={6} md={3} component="div">
              <Card raised>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Projected Month-End Spend
                  </Typography>
                  <Typography variant="h5">
                    {overview?.projected_month_end_spend !== undefined
                      ? `$${overview.projected_month_end_spend.toFixed(2)}`
                      : 'N/A'}
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
          <Grid item xs={12} sm={6} md={3} component="div">
            <FormControl
              fullWidth
              variant="outlined"
              sx={{ minWidth: '240px', maxWidth: '240px', height: '56px' }}
            >
              <InputLabel id="project-select-label">Project ID</InputLabel>
              <Select
                labelId="project-select-label"
                id="project-select"
                value={projectFilter}
                label="Project ID"
                onChange={(e) => setProjectFilter(e.target.value as string)}
                disabled={distinctProjectsLoading}
                MenuProps={{ PaperProps: { style: { maxHeight: 480 } } }} // Set max height for dropdown
              >
                <MenuItem value="">
                  <em>All</em>
                </MenuItem>
                {distinctProjectsLoading ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} /> Loading...
                  </MenuItem>
                ) : distinctProjectsError ? (
                  <MenuItem disabled>Error loading projects</MenuItem>
                ) : (
                  distinctProjects.map((project) => (
                    <MenuItem key={project} value={project}>
                      {project}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <FormControl
              fullWidth
              variant="outlined"
              sx={{ minWidth: '240px', maxWidth: '240px', height: '56px' }}
            >
              <InputLabel id="service-select-label">Service</InputLabel>
              <Select
                labelId="service-select-label"
                id="service-select"
                value={serviceFilter}
                label="Service"
                onChange={(e) => setServiceFilter(e.target.value as string)}
                disabled={distinctServicesLoading}
                MenuProps={{ PaperProps: { style: { maxHeight: 480 } } }} // Set max height for dropdown
              >
                <MenuItem value="">
                  <em>All</em>
                </MenuItem>
                {distinctServicesLoading ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} /> Loading...
                  </MenuItem>
                ) : distinctServicesError ? (
                  <MenuItem disabled>Error loading services</MenuItem>
                ) : (
                  distinctServices.map((service) => (
                    <MenuItem key={service} value={service}>
                      {service}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <FormControl
              fullWidth
              variant="outlined"
              sx={{ minWidth: '240px', maxWidth: '240px', height: '56px' }}
            >
              <InputLabel id="sku-select-label">SKU</InputLabel>
              <Select
                labelId="sku-select-label"
                id="sku-select"
                value={skuFilter}
                label="SKU"
                onChange={(e) => setSkuFilter(e.target.value as string)}
                disabled={distinctSkusLoading}
                MenuProps={{ PaperProps: { style: { maxHeight: 480 } } }} // Set max height for dropdown
              >
                <MenuItem value="">
                  <em>All</em>
                </MenuItem>
                {distinctSkusLoading ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} /> Loading...
                  </MenuItem>
                ) : distinctSkusError ? (
                  <MenuItem disabled>Error loading SKUs</MenuItem>
                ) : (
                  distinctSkus.map((sku) => (
                    <MenuItem key={sku} value={sku}>
                      {sku}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <TextField
              label="Start Date"
              type="date"
              variant="outlined"
              fullWidth
              sx={{ minWidth: '240px', maxWidth: '240px' }}
              InputLabelProps={{ shrink: true }}
              value={startDateFilter}
              onChange={(e) => setStartDateFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <TextField
              label="End Date"
              type="date"
              variant="outlined"
              fullWidth
              sx={{ minWidth: '240px', maxWidth: '240px' }}
              InputLabelProps={{ shrink: true }}
              value={endDateFilter}
              onChange={(e) => setEndDateFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
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
          <CircularProgress />
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
                        <TableCell align="right">
                          {row.usage_amount?.toFixed(2) || 'N/A'} {row.usage_unit || ''}
                        </TableCell>
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

      {/* AI-Powered FinOps Insights Panel */}
      <AIInsightPanel
        currentProjectFilter={projectFilter}
        currentServiceFilter={serviceFilter}
        currentSkuFilter={skuFilter}
        currentStartDateFilter={startDateFilter}
        currentEndDateFilter={endDateFilter}
      />
    </Container>
  );
};

export default DashboardPage;
