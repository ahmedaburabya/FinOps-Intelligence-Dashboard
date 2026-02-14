// frontend/src/theme/theme.ts
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // A shade of blue
    },
    secondary: {
      main: '#dc004e', // A shade of red
    },
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    // Add other typography variants as needed
  },
  // You can customize other aspects like spacing, breakpoints, components
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true, // Example: disable elevation for all buttons
      },
      styleOverrides: {
        root: {
          borderRadius: 8, // Example: more rounded buttons
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#20232a', // Darker app bar
        },
      },
    },
  },
});

export default theme;
