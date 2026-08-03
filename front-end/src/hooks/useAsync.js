import { useState, useEffect } from "react";

export default function useAsync(handler, immediate = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const act = (...args) => {
    setLoading(true);
    setError(null);
    return handler(...args)
      .then((result) => {
        setData(result);
        return result;
      })
      .catch((requestError) => {
        setError(requestError);
        throw requestError;
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (immediate) {
      act().catch(() => {});
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
