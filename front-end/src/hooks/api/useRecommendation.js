import useAsync from "../useAsync";

import * as service from "../../services/recommendations";

export default function useRecommendation() {
  const { data, loading, error, act } = useAsync(service.get);

  const update = async (id) => {
    try {
      return await act(id);
    } catch {
      return act();
    }
  };

  return {
    recommendation: data,
    loadingRecommendation: loading,
    errorLoadingRecommendation: error,
    getRecommendation: act,
    updateRecommendation: update
  };
}
