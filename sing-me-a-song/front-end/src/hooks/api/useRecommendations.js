import useAsync from "../useAsync";
import * as service from "../../services/recommendations";

export default function useRecommendations() {
  const { data, loading, act, error } = useAsync(service.list);

  return {
    recommendations: data,
    errorRecommendations: error,
    loadingRecommendations: loading,
    listRecommendations: act
  };
}
