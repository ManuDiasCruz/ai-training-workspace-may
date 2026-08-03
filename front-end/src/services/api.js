import axios from "axios";

const configuredBaseUrl = process.env.REACT_APP_API_BASE_URL?.replace(/\/+$/, "");
const defaultBaseUrl = process.env.NODE_ENV === "production"
  ? ""
  : "http://localhost:5000";

const instance = axios.create({
  baseURL: configuredBaseUrl || defaultBaseUrl,
  timeout: 10000,
});

export default instance;
