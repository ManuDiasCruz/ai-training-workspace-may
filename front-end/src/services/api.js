import axios from "axios";

// Without a fallback, a missing REACT_APP_API_BASE_URL leaves baseURL
// undefined and every request silently targets the dev server itself
// (http://localhost:3000/recommendations -> 404), which looks like a broken
// app rather than a missing configuration value.
const DEFAULT_BASE_URL = "http://localhost:5000";

const baseURL = process.env.REACT_APP_API_BASE_URL || DEFAULT_BASE_URL;

if (!process.env.REACT_APP_API_BASE_URL) {
  console.warn(
    `REACT_APP_API_BASE_URL is not set; falling back to ${DEFAULT_BASE_URL}. ` +
      "Copy .env.example to .env to configure the API URL."
  );
}

const instance = axios.create({
  baseURL,
});

export default instance;
