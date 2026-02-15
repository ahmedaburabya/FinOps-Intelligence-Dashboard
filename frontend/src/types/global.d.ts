declare global {
  interface Window {
    _env_?: {
      VITE_API_BASE_URL?: string;
    };
  }
}

export {}; // This ensures the file is treated as a module.
