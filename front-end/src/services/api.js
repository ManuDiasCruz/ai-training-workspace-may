import axios from "axios";

const configuredBaseUrl = process.env.REACT_APP_API_BASE_URL;
const instance = axios.create({
  baseURL: configuredBaseUrl || (process.env.NODE_ENV === "development" ? "http://localhost:5000" : ""),
  timeout: 15000,
});

export default instance;
