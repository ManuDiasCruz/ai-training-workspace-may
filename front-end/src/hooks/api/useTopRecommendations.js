import useAsync from "../useAsync";
import * as service from "../../services/recommendations";

export default function useTopRecommendations() {
  const { data, loading, act, error } = useAsync(service.listTop);

  return {
    recommendations: data,
    loadingRecommendations: loading,
    recommendationsError: error,
    listRecommendations: act
  };
}
