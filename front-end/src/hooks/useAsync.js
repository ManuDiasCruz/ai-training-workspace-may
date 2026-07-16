import { useCallback, useEffect, useState } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const act = useCallback(async (...args) => {
    setLoading(true);
    setError(null);

    try {
      const data = await handler(...args);
      setData(data);
      return data;
    } catch (error) {
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [handler]);

  useEffect(() => {
    if (immediate) {
      act().catch(() => undefined);
    }
  }, [act, immediate]);

  return {
    data,
    loading,
    error,
    act
  };
}
