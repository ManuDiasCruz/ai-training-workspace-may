import { useCallback, useEffect, useRef, useState } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mounted = useRef(true);
  const latestRequest = useRef(0);

  const act = useCallback(async (...args) => {
    const request = ++latestRequest.current;
    setLoading(true);
    setError(null);
    try {
      const result = await handler(...args);
      if (mounted.current && request === latestRequest.current) setData(result);
      return { ok: true, data: result };
    } catch (requestError) {
      if (mounted.current && request === latestRequest.current) setError(requestError);
      return { ok: false, error: requestError };
    } finally {
      if (mounted.current && request === latestRequest.current) setLoading(false);
    }
  }, [handler]);

  useEffect(() => {
    mounted.current = true;
    if (immediate) {
      act();
    }
    return () => {
      mounted.current = false;
    };
  }, [act, immediate]);

  return {
    data,
    loading,
    error,
    act
  };
}
