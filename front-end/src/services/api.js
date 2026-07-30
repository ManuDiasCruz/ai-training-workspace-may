import axios from "axios";

// When REACT_APP_API_BASE_URL is unset, axios falls back to the page origin
// and every request 404s against the dev server. Default to the port the
// back-end listens on so a fresh clone works without any .env file.
const baseURL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

const instance = axios.create({
  baseURL,
});

export default instance;
