import useAsync from "../useAsync";

import * as service from "../../services/recommendations";

export default function useRecommendation() {
  const { data, error, act } = useAsync(service.get);

  return {
    recommendation: data,
    recommendationError: error,
    getRecommendation: act
  };
}
