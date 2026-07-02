import useAsync from "../useAsync";
import * as service from "../../services/recommendations";

export default function useTopRecommendations() {
  const { data, loading, error, act } = useAsync(service.listTop);

  return {
    recommendations: data,
    loadingRecommendations: loading,
    listRecommendations: act,
    recommendationsError: error,
  };
}
