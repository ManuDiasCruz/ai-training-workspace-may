import axios from "axios";

// REACT_APP_API_BASE_URL is inlined at build time. When it is missing axios
// falls back to relative URLs, so every request silently hits the CRA dev
// server instead of the API and the whole app renders an endless "Loading...".
// Fall back to the documented local API address and make the misconfiguration
// visible in the console instead of failing mysteriously.
const DEFAULT_BASE_URL = "http://localhost:5000";

export const baseURL = (
  process.env.REACT_APP_API_BASE_URL || DEFAULT_BASE_URL
).replace(/\/+$/, "");

if (!process.env.REACT_APP_API_BASE_URL) {
  console.warn(
    `[sing-me-a-song] REACT_APP_API_BASE_URL is not set, falling back to ${DEFAULT_BASE_URL}. ` +
      "Copy front-end/.env.example to front-end/.env to configure it."
  );
}

const instance = axios.create({
  baseURL
});

export default instance;
