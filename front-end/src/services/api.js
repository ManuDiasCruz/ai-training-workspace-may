import axios from "axios";

const defaultBaseUrl =
  process.env.NODE_ENV === "development" ? "http://localhost:5000" : "";

const instance = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || defaultBaseUrl
});

export default instance;
