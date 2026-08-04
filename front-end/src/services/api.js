import axios from "axios";

const instance = axios.create({
  // An unset value intentionally uses the current origin in the production deployment.
  baseURL: process.env.REACT_APP_API_BASE_URL || undefined,
  timeout: 15000,
});

export default instance;
