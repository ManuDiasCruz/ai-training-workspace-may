import { useState, useEffect } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const act = (...args) => {
    setLoading(true);
    setError(null);
    return handler(...args).then((data) => {
      setData(data);
      setLoading(false);
      return data;
    }).catch((error) => {
      setError(error);
      setLoading(false);
      throw error;
    });
  };

  useEffect(() => {
    if (immediate) {
      act().catch(() => {
        // Errors are exposed through the hook and rendered by page components.
      });
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    data,
    loading,
    error,
    act
  };
}
