import { useState, useEffect } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Resolves with the handler's result, or with null when it failed
  // (the failure is also exposed through `error`).
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
      return null;
    });
  };

  useEffect(() => {
    if (immediate) {
      act();
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
