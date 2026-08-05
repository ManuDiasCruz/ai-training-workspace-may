import { useState, useEffect, useCallback } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const act = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await handler(...args);
      setData(result);
      return result;
    } catch (error) {
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [handler]);

  useEffect(() => {
    if (immediate) {
      act().catch(() => {});
    }

  }, [act, immediate]);

  return {
    data,
    loading,
    error,
    act
  };
}
