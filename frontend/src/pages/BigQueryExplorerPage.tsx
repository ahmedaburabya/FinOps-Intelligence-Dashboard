// frontend/src/pages/BigQueryExplorerPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  CircularProgress,
  Table,
  TableContainer,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Paper,
  Alert,
  Tooltip, // Added Tooltip
} from '@mui/material';
import { finopsApi } from '../services';
import LoadingSpinner from '../components/common/LoadingSpinner';
import SnackbarAlert from '../components/common/SnackbarAlert';
import type { BigQueryTableDataRow } from '../types/bigquery';

const BigQueryExplorerPage: React.FC = () => {
  const [datasets, setDatasets] = useState<string[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [tableData, setTableData] = useState<BigQueryTableDataRow[]>([]);
  const [tableDataLimit, setTableDataLimit] = useState<number>(10);
  const [nextPageToken, setNextPageToken] = useState<string | null>(null); // New state

  const [loadingDatasets, setLoadingDatasets] = useState<boolean>(true);
  const [loadingTables, setLoadingTables] = useState<boolean>(false);
  const [loadingTableData, setLoadingTableData] = useState<boolean>(false);
  const [ingestionLoading, setIngestionLoading] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<
    'success' | 'error' | 'info' | 'warning'
  >('success');

  // Ingestion state
  const [ingestDatasetId, setIngestDatasetId] = useState<string>('finopsDS');
  const [ingestTableId, setIngestTableId] = useState<string>(
    'gcp_billing_export_resource_v1_01F185_0AA423_C9BA8A',
  );
  const [ingestStartDate, setIngestStartDate] = useState<string>('');
  const [ingestEndDate, setIngestEndDate] = useState<string>('');

  // Fetch Datasets
  useEffect(() => {
    const fetchDatasets = async (token: string | null = null) => {
      setLoadingDatasets(true);
      setError(null);
      try {
        const response = await finopsApi.listBigQueryDatasets({ page_token: token });
        if (token) {
          setDatasets((prevDatasets) => [...prevDatasets, ...response.datasets]);
        } else {
          setDatasets(response.datasets);
        }
        setNextPageToken(response.next_page_token);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch BigQuery datasets.');
      } finally {
        setLoadingDatasets(false);
      }
    };
    fetchDatasets(); // Initial fetch
  }, []);

  // Fetch Tables when dataset changes
  useEffect(() => {
    const fetchTables = async () => {
      if (selectedDataset) {
        setLoadingTables(true);
        setError(null);
        setSelectedTable('');
        setTableData([]);
        try {
          const response = await finopsApi.listBigQueryTables(selectedDataset);
          setTables(response);
        } catch (err: any) {
          setError(
            err.response?.data?.detail || `Failed to fetch tables for dataset ${selectedDataset}.`,
          );
        } finally {
          setLoadingTables(false);
        }
      }
    };
    fetchTables();
  }, [selectedDataset]);

  // Fetch Table Data when table changes
  useEffect(() => {
    const fetchTableData = async () => {
      if (selectedDataset && selectedTable) {
        setLoadingTableData(true);
        setError(null);
        try {
          const response = await finopsApi.readBigQueryTableData(
            selectedDataset,
            selectedTable,
            tableDataLimit,
          );
          setTableData(response);
        } catch (err: any) {
          setError(
            err.response?.data?.detail || `Failed to fetch data for table ${selectedTable}.`,
          );
        } finally {
          setLoadingTableData(false);
        }
      }
    };
    fetchTableData();
  }, [selectedDataset, selectedTable, tableDataLimit]);

  const handleDatasetChange = (event: any) => {
    setSelectedDataset(event.target.value);
    setSelectedTable(''); // Clear selected table when dataset changes
  };

  const handleTableChange = (event: any) => {
    setSelectedTable(event.target.value);
  };

  const handleIngestData = async () => {
    if (!ingestDatasetId || !ingestTableId) {
      setSnackbarMessage('Please select a dataset and table for ingestion.');
      setSnackbarSeverity('warning');
      setSnackbarOpen(true);
      return;
    }
    setIngestionLoading(true);
    setError(null);
    try {
      const response = await finopsApi.ingestBigQueryBillingData({
        dataset_id: ingestDatasetId,
        table_id: ingestTableId,
        start_date: ingestStartDate || undefined,
        end_date: ingestEndDate || undefined,
      });
      setSnackbarMessage(response.message);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (err: any) {
      console.error('Ingestion error:', err);
      setError(err.response?.data?.detail || 'Failed to ingest BigQuery data.');
      setSnackbarMessage(err.response?.data?.detail || 'Failed to ingest BigQuery data.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setIngestionLoading(false);
    }
  };

  const handleSnackbarClose = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  if (loadingDatasets) {
    return <LoadingSpinner message="Loading BigQuery resources..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        BigQuery Explorer & Ingestion
      </Typography>

      <SnackbarAlert
        open={snackbarOpen}
        message={snackbarMessage}
        severity={snackbarSeverity}
        onClose={handleSnackbarClose}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Dataset Selection */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Select BigQuery Dataset
        </Typography>
        <Tooltip title="Select a BigQuery dataset to explore its tables and data.">
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="dataset-select-label">Dataset</InputLabel>
            <Select
              labelId="dataset-select-label"
              id="dataset-select"
              value={selectedDataset}
              label="Dataset"
              onChange={handleDatasetChange}
              disabled={loadingDatasets}
            >
              {datasets.length > 0 ? (
                datasets.map((ds) => (
                  <MenuItem key={ds} value={ds}>
                    {ds}
                  </MenuItem>
                ))
              ) : (
                <MenuItem value="" disabled>
                  No datasets found
                </MenuItem>
              )}
            </Select>
          </FormControl>
        </Tooltip>

        {nextPageToken && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, mb: 2 }}>
            <Button
              variant="outlined"
              onClick={() => fetchDatasets(nextPageToken)} // Call fetchDatasets with next_page_token
              disabled={loadingDatasets}
              startIcon={loadingDatasets ? <CircularProgress size={20} /> : null}
            >
              {loadingDatasets ? 'Loading More...' : 'Load More Datasets'}
            </Button>
          </Box>
        )}

        {/* Table Selection */}
        {selectedDataset && (
          <Tooltip title="Select a table within the chosen BigQuery dataset to preview its data.">
            <FormControl fullWidth sx={{ my: 2 }}>
              <InputLabel id="table-select-label">Table</InputLabel>
              <Select
                labelId="table-select-label"
                id="table-select"
                value={selectedTable}
                label="Table"
                onChange={handleTableChange}
                disabled={loadingTables}
              >
                {loadingTables ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} sx={{ mr: 1 }} /> Loading tables...
                  </MenuItem>
                ) : tables.length > 0 ? (
                  tables.map((tbl) => (
                    <MenuItem key={tbl} value={tbl}>
                      {tbl}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem value="" disabled>
                    No tables found
                  </MenuItem>
                )}
              </Select>
            </FormControl>
          </Tooltip>
        )}
      </Box>

      {/* Display Table Data */}
      {selectedTable && (
        <Box sx={{ my: 4 }}>
          <Typography variant="h5" component="h2" gutterBottom>
            Data Preview: {selectedDataset}.{selectedTable}
          </Typography>
          <Tooltip title="Specify the maximum number of rows to retrieve from the selected BigQuery table.">
            <TextField
              label="Limit Rows"
              type="number"
              value={tableDataLimit}
              onChange={(e) => setTableDataLimit(Number(e.target.value))}
              inputProps={{ min: 1, max: 100 }}
              sx={{ mb: 2 }}
            />
          </Tooltip>
          {loadingTableData ? (
            <LoadingSpinner message="Loading table data..." />
          ) : tableData.length > 0 ? (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {Object.keys(tableData[0]).map((key) => (
                      <TableCell key={key}>{key}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tableData.map((row, index) => (
                    <TableRow key={index}>
                      {Object.values(row).map((value, idx) => (
                        <TableCell key={idx}>
                          {typeof value === 'object' && value !== null
                            ? JSON.stringify(value)
                            : String(value)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">No data found for this table or it's empty.</Alert>
          )}
        </Box>
      )}

      {/* Ingest BigQuery Data to PostgreSQL */}
      <Box sx={{ my: 4, p: 3, border: '1px solid #e0e0e0', borderRadius: 2 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Ingest BigQuery Billing Data to PostgreSQL
        </Typography>
        <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Tooltip title="The ID of the BigQuery dataset from which billing data will be ingested. This field is read-only.">
            <TextField
              label="BigQuery Dataset ID"
              variant="outlined"
              fullWidth
              value="finopsDS"
              InputProps={{ readOnly: true }}
              required
            />
          </Tooltip>
          <Tooltip title="The ID of the BigQuery table containing the billing export data. This field is read-only.">
            <TextField
              label="BigQuery Table ID"
              variant="outlined"
              fullWidth
              value="gcp_billing_export_resource_v1_01F185_0AA423_C9BA8A"
              InputProps={{ readOnly: true }}
              required
            />
          </Tooltip>
          <TextField
            label="Start Date (YYYY-MM-DD)"
            type="date"
            variant="outlined"
            fullWidth
            InputLabelProps={{ shrink: true }}
            value={ingestStartDate}
            onChange={(e) => setIngestStartDate(e.target.value)}
          />
          <TextField
            label="End Date (YYYY-MM-DD)"
            type="date"
            variant="outlined"
            fullWidth
            InputLabelProps={{ shrink: true }}
            value={ingestEndDate}
            onChange={(e) => setIngestEndDate(e.target.value)}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleIngestData}
            disabled={ingestionLoading || !ingestDatasetId || !ingestTableId}
          >
            {ingestionLoading ? <CircularProgress size={24} /> : 'Ingest Data'}
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default BigQueryExplorerPage;
