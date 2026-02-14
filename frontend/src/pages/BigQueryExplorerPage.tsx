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

  const [loadingDatasets, setLoadingDatasets] = useState<boolean>(true);
  const [loadingTables, setLoadingTables] = useState<boolean>(false);
  const [loadingTableData, setLoadingTableData] = useState<boolean>(false);
  const [ingestionLoading, setIngestionLoading] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');

  // Ingestion state
  const [ingestDatasetId, setIngestDatasetId] = useState<string>('');
  const [ingestTableId, setIngestTableId] = useState<string>('');
  const [ingestStartDate, setIngestStartDate] = useState<string>('');
  const [ingestEndDate, setIngestEndDate] = useState<string>('');


  // Fetch Datasets
  useEffect(() => {
    const fetchDatasets = async () => {
      setLoadingDatasets(true);
      setError(null);
      try {
        const response = await finopsApi.listBigQueryDatasets();
        setDatasets(response);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch BigQuery datasets.');
      } finally {
        setLoadingDatasets(false);
      }
    };
    fetchDatasets();
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
          setError(err.response?.data?.detail || `Failed to fetch tables for dataset ${selectedDataset}.`);
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
          const response = await finopsApi.readBigQueryTableData(selectedDataset, selectedTable, tableDataLimit);
          setTableData(response);
        } catch (err: any) {
          setError(err.response?.data?.detail || `Failed to fetch data for table ${selectedTable}.`);
        } finally {
          setLoadingTableData(false);
        }
      }
    };
    fetchTableData();
  }, [selectedDataset, selectedTable, tableDataLimit]);

  const handleDatasetChange = (event: any) => {
    setSelectedDataset(event.target.value);
    setIngestDatasetId(event.target.value); // Sync for ingestion form
  };

  const handleTableChange = (event: any) => {
    setSelectedTable(event.target.value);
    setIngestTableId(event.target.value); // Sync for ingestion form
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

  const handleSnackbarClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
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

        {/* Table Selection */}
        {selectedDataset && (
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
        )}
      </Box>

      {/* Display Table Data */}
      {selectedTable && (
        <Box sx={{ my: 4 }}>
          <Typography variant="h5" component="h2" gutterBottom>
            Data Preview: {selectedDataset}.{selectedTable}
          </Typography>
          <TextField
            label="Limit Rows"
            type="number"
            value={tableDataLimit}
            onChange={(e) => setTableDataLimit(Number(e.target.value))}
            inputProps={{ min: 1, max: 100 }}
            sx={{ mb: 2 }}
          />
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
          <TextField
            label="BigQuery Dataset ID"
            variant="outlined"
            fullWidth
            value={ingestDatasetId}
            onChange={(e) => setIngestDatasetId(e.target.value)}
            required
          />
          <TextField
            label="BigQuery Table ID"
            variant="outlined"
            fullWidth
            value={ingestTableId}
            onChange={(e) => setIngestTableId(e.target.value)}
            required
          />
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
