import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { BarChart, LineChart } from '@mui/x-charts'; // Removed PieChart, kept BarChart and LineChart
import type { AggregatedCostData } from '~/types/finops';

interface CostChartsProps {
  costData: AggregatedCostData[];
  projectCostData: AggregatedCostData[];
}

const CostCharts: React.FC<CostChartsProps> = ({ costData, projectCostData }) => {
  // Process data for Cost by Service (Bar Chart) - Reverted to Bar Chart logic
  const serviceCostMap = new Map<string, number>();
  costData.forEach((item) => {
    const currentCost = serviceCostMap.get(item.service) || 0;
    serviceCostMap.set(item.service, currentCost + item.cost);
  });

  const serviceNames = Array.from(serviceCostMap.keys());
  const serviceCosts = Array.from(serviceCostMap.values());

  // Process data for Cost by Project (Bar Chart)
  const projectCostMap = new Map<string, number>();
  projectCostData.forEach((item) => { // Use projectCostData here
    // Only include items with a defined project
    if (item.project) {
      const currentCost = projectCostMap.get(item.project) || 0;
      projectCostMap.set(item.project, currentCost + item.cost);
    }
  });

  const projectNames = Array.from(projectCostMap.keys());
  const projectCosts = Array.from(projectCostMap.values());

  // Process data for Cost Over Time (Line Chart)
  const dailyCostMap = new Map<string, number>();
  costData.forEach((item) => {
    const date = new Date(item.time_period).toLocaleDateString(); // Group by date
    const currentCost = dailyCostMap.get(date) || 0;
    dailyCostMap.set(date, currentCost + item.cost);
  });

  // Sort dates for the line chart
  const sortedDates = Array.from(dailyCostMap.keys()).sort((a, b) => {
    const [aMonth, aDay, aYear] = a.split('/').map(Number);
    const [bMonth, bDay, bYear] = b.split('/').map(Number);
    return new Date(aYear, aMonth - 1, aDay).getTime() - new Date(bYear, bMonth - 1, bDay).getTime();
  });
  const dailyCosts = sortedDates.map(date => dailyCostMap.get(date) || 0);

  // Determine chart dimensions dynamically or set a fixed size
  const chartWidth = Math.max(300, serviceNames.length * 30); // Adjust width based on number of bars
  const chartHeight = 200;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Paper elevation={3} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Cost by Project
          </Typography>
          {projectNames.length > 0 ? (
            <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-start' }}>
              <BarChart
                series={[{ data: projectCosts, label: 'Cost (USD)' }]}
                height={chartHeight}
                width={chartWidth} // Use the same dynamic width calculation as for services
                xAxis={[{ scaleType: 'band', data: projectNames }]}
                yAxis={[{ label: 'Total Cost ($)' }]}
                margin={{ top: 10, bottom: 30, left: 50, right: 10 }}
                slotProps={{
                  legend: {
                    direction: 'row',
                    position: { vertical: 'bottom', horizontal: 'middle' },
                    padding: 0,
                  },
                }}
              />
            </Box>
          ) : (
            <Typography>No project cost data available for charting.</Typography>
          )}
        </Paper>
      </Grid>
      <Grid item xs={12} md={6}>
        <Paper elevation={3} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Cost by Service
          </Typography>
          {serviceNames.length > 0 ? ( // Reverted condition to serviceNames
            <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-start' }}>
              <BarChart // Reverted to BarChart
                series={[{ data: serviceCosts, label: 'Cost (USD)' }]} // Reverted series data
                height={chartHeight}
                width={chartWidth} // Reverted width to chartWidth (dynamic)
                xAxis={[{ scaleType: 'band', data: serviceNames }]} // Reverted xAxis
                yAxis={[{ label: 'Total Cost ($)' }]} // Reverted yAxis
                margin={{ top: 10, bottom: 30, left: 50, right: 10 }}
                slotProps={{
                  legend: {
                    direction: 'row',
                    position: { vertical: 'bottom', horizontal: 'middle' },
                    padding: 0,
                  },
                }}
              />
            </Box>
          ) : (
            <Typography>No service cost data available for charting.</Typography>
          )}
        </Paper>
      </Grid>
      <Grid item xs={12} md={6}>
        <Paper elevation={3} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Cost Over Time
          </Typography>
          {sortedDates.length > 0 ? (
            <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-start' }}>
              <LineChart
                series={[{ data: dailyCosts, label: 'Cost (USD)' }]}
                height={chartHeight}
                width={400}
                xAxis={[{ scaleType: 'point', data: sortedDates }]}
                yAxis={[{ label: 'Total Cost ($)' }]}
                margin={{ top: 10, bottom: 30, left: 50, right: 10 }}
                slotProps={{
                  legend: {
                    direction: 'row',
                    position: { vertical: 'bottom', horizontal: 'middle' },
                    padding: 0,
                  },
                }}
              />
            </Box>
          ) : (
            <Typography>No daily cost data available for charting.</Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
};

export default CostCharts;
