import axios from "axios";

const configuredBaseUrl = process.env.REACT_APP_API_BASE_URL?.trim();

const instance = axios.create({
  baseURL: configuredBaseUrl || (process.env.NODE_ENV === "development" ? "http://localhost:5000" : undefined)
});

export default instance;
