import useAsync from "../useAsync";

import * as service from "../../services/recommendations";

export default function useRecommendation() {
  const { data, loading, error, act } = useAsync(service.get);

  return {
    recommendation: data,
    loadingRecommendation: loading,
    getRecommendation: act,
    recommendationError: error,
  };
}
