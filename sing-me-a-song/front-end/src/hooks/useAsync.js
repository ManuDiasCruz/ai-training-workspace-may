import { useState, useEffect, useCallback, useRef } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const mounted = useRef(true);
  const request = useRef(0);
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  const act = useCallback(async (...args) => {
    const current = ++request.current;
    setLoading(true);
    setError(null);
    try {
      const result = await handlerRef.current(...args);
      if (mounted.current && current === request.current) setData(result);
      return result;
    } catch (failure) {
      if (mounted.current && current === request.current) setError(failure);
      throw failure;
    } finally {
      if (mounted.current && current === request.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    if (immediate) act().catch(() => {}); // Error is exposed to the rendering component.
    return () => { mounted.current = false; };
  }, [act, immediate]);

  return {
    data,
    loading,
    error,
    act
  };
}
