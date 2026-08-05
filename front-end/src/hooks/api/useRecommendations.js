import useAsync from "../useAsync";
import * as service from "../../services/recommendations";

export default function useRecommendations() {
  const { data, loading, error, act } = useAsync(service.list);

  return {
    recommendations: data,
    loadingRecommendations: loading,
    recommendationsError: error,
    listRecommendations: act
  };
}
