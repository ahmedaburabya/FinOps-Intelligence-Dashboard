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
  Tooltip, // Added Tooltip
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
import CostCharts from '~/components/CostCharts'; // Import the new CostCharts component

const DashboardPage: React.FC = () => {
  const [projectFilter, setProjectFilter] = useState<string>('');
  const [serviceFilter, setServiceFilter] = useState<string>('');
  const [skuFilter, setSkuFilter] = useState<string>('');
  const [startDateFilter, setStartDateFilter] = useState<string>('');
  const [endDateFilter, setEndDateFilter] = useState<string>('');

  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, _setItemsPerPage] = useState<number>(10); // Renamed to silence unused error

  const {
    overview,
    loading: overviewLoading,
    error: overviewError,
    refetchOverview,
  } = useFinopsOverview();

  // Fetch initial overview data on component mount
  useEffect(() => {
    refetchOverview(undefined);
  }, []); // Empty dependency array means this runs once on mount

  const {
    costData,
    totalCount,
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

  // New hook for "Cost by Project" chart (only filtered by project and date)
  const {
    costData: projectChartCostData,
    loading: projectChartCostDataLoading,
    error: projectChartCostDataError,
    refetchCostData: refetchProjectChartCostData,
  } = useAggregatedCostData({
    // No skip/limit for chart data, fetch all relevant data
    service: undefined, // Ignore service filter
    sku: undefined, // Ignore SKU filter
    project: projectFilter || undefined, // Only apply project filter
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
    refetchOverview(projectFilter || undefined); // Pass the current projectFilter
    refetchProjectChartCostData(); // Refetch project-specific chart data
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

  if (
    overviewLoading &&
    costDataLoading &&
    distinctServicesLoading &&
    distinctProjectsLoading &&
    distinctSkusLoading &&
    projectChartCostDataLoading
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
        distinctSkusError ||
        projectChartCostDataError) && ( // Added projectChartCostDataError
        <SnackbarAlert
          open={true} // Always open if there's an error
          message={
            overviewError?.detail ||
            costDataError?.detail ||
            llmSummaryError ||
            distinctServicesError?.message || // Display distinctServicesError message
            distinctProjectsError?.message || // Display distinctProjectsError message
            distinctSkusError?.message || // Display distinctSkusError message
            projectChartCostDataError?.message || // Display projectChartCostDataError message
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
            projectChartCostDataError ? (projectChartCostDataError.message = null) : null; // Clear projectChartCostDataError
          }}
          autoHideDuration={undefined} // Changed from null to undefined
        />
      )}

      {/* Filters for Aggregated Cost Data */}
      <Box sx={{ my: 4, p: 3, border: '1px solid #e0e0e0', borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filter Aggregated Cost Data
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3} component="div">
            <Tooltip title="Filter data by a specific Google Cloud Project ID.">
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
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <Tooltip title="Filter data by a specific Google Cloud Service (e.g., Compute Engine, BigQuery).">
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
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <Tooltip title="Filter data by a specific Stock Keeping Unit (SKU).">
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
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <Tooltip title="Filter aggregated cost data from this start date (inclusive).">
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
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <Tooltip title="Filter aggregated cost data up to this end date (inclusive).">
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
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={3} component="div">
            <Tooltip title="Apply the selected filters to update the aggregated cost data and financial overview.">
              <Button variant="contained" onClick={handleApplyFilters} fullWidth>
                Apply Filters
              </Button>
            </Tooltip>
          </Grid>
        </Grid>
      </Box>

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
              <Tooltip title="Total cost incurred in the current calendar month up to today.">
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
              </Tooltip>
            </Grid>
            <Grid item xs={12} sm={6} md={3} component="div">
              <Tooltip title="An estimated total monthly spend based on recent daily average consumption (e.g., last 30 days).">
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
              </Tooltip>
            </Grid>
            {/* New card for Daily Burn Rate MTD */}
            <Grid item xs={12} sm={6} md={3} component="div">
              <Tooltip title="Average daily spend in the current calendar month.">
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
              </Tooltip>
            </Grid>
            {/* New card for Projected Month-End Spend */}
            <Grid item xs={12} sm={6} md={3} component="div">
              <Tooltip title="Estimated total spend for the current month based on current Month-to-Date spend and daily burn rate.">
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
              </Tooltip>
            </Grid>
            {/* Add more overview cards here if needed */}
          </Grid>
        )}
        {costData && costData.length > 0 && (
          <Box
            sx={{ mt: 4, display: 'flex', justifyContent: 'flex-start', gap: 4, flexWrap: 'wrap' }}
          >
            <CostCharts costData={costData} projectCostData={projectChartCostData} />
          </Box>
        )}
      </Box>

      {/* Aggregated Cost Data Table */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Aggregated Cost Data
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
          Total Records: {costDataLoading ? 'Loading...' : totalCount}
        </Typography>
        {costDataLoading ? (
          <CircularProgress />
        ) : (
          <>
            <TableContainer component={Paper}>
              <Table sx={{ minWidth: 650 }} aria-label="aggregated cost data table">
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <Tooltip title="Unique identifier for the aggregated cost data record.">
                        ID
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Google Cloud service associated with the cost (e.g., Compute Engine).">
                        Service
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Google Cloud project ID where the cost was incurred.">
                        Project
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Stock Keeping Unit: a specific product or service item.">
                        SKU
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Aggregated cost for the specified time period in USD.">
                        Cost (USD)
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Total amount of usage for the SKU during the time period.">
                        Usage Amount
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="The specific day or period the cost data aggregates.">
                        Time Period
                      </Tooltip>
                    </TableCell>
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
                count={Math.ceil(totalCount / itemsPerPage)} // Use totalCount from hook
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          </>
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
