import { useState, useEffect, useCallback, useRef } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestId = useRef(0);
  const act = useCallback(async (...args) => {
    const current = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const result = await handler(...args);
      if (current === requestId.current) setData(result);
      return { success: true, data: result };
    } catch (error) {
      if (current === requestId.current) { setError(error); setData(null); }
      return { success: false, error };
    } finally {
      if (current === requestId.current) setLoading(false);
    }
  }, [handler]);
  useEffect(() => {
    if (immediate) act();
    return () => { requestId.current += 1; };
  }, [act, immediate]);
  return { data, loading, error, act };
}
