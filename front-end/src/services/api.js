import axios from "axios";

// REACT_APP_API_BASE_URL is baked in at build time. Falling back to the
// default local API port keeps `npm start` working before any .env exists,
// instead of silently sending every request to the CRA dev server itself.
const baseURL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

const instance = axios.create({
  baseURL
});

export default instance;
