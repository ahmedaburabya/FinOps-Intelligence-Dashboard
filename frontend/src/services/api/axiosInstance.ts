// frontend/src/services/api/axiosInstance.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
  console.error("VITE_API_BASE_URL is not defined. Please check your .env file.");
  throw new Error("VITE_API_BASE_URL is not defined. Cannot proceed with API calls.");
}

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add request or response interceptors
axiosInstance.interceptors.request.use(
  (config) => {
    // Example: Add an authorization token if available
    // const token = localStorage.getItem('authToken');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Example: Handle global errors like 401 Unauthorized
    if (error.response && error.response.status === 401) {
      console.error("Unauthorized access - redirecting to login or refreshing token.");
      // You might trigger a global event here or redirect
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
