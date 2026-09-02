import axios from "axios";

function resolveBaseURL() {
  // The static (GitHub Pages) build can point at any back-end without a
  // rebuild: ?api=https://my-backend overrides the base URL and persists.
  try {
    const fromQuery = new URLSearchParams(window.location.search).get("api");
    if (fromQuery) {
      localStorage.setItem("apiBaseUrl", fromQuery);
      return fromQuery;
    }

    const stored = localStorage.getItem("apiBaseUrl");
    if (stored) return stored;
  } catch (_) {
    // storage unavailable: fall through to the build-time default
  }

  return process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";
}

const instance = axios.create({
  baseURL: resolveBaseURL()
});

export default instance;
