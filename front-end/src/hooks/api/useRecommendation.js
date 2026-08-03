import useAsync from "../useAsync";

import * as service from "../../services/recommendations";

export default function useRecommendation() {
  const { data, loading, error, act } = useAsync(service.get);

  const update = (id) => {
    act(id);
  };

  return {
    recommendation: data,
    loadingRecommendation: loading,
    recommendationError: error,
    getRecommendation: act,
    updateRecommendation: update
  };
}
