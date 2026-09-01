import useAsync from "../useAsync";

import * as service from "../../services/recommendations";

export default function useRecommendation() {
  const { data, loading, act, error } = useAsync(service.get);

  return {
    recommendation: data,
    error,
    loadingRecommendation: loading,
    getRecommendation: act,
    updateRecommendation: act
  };
}
