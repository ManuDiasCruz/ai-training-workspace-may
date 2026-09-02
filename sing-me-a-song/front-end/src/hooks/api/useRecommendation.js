import useAsync from "../useAsync";

import * as service from "../../services/recommendations";

export default function useRecommendation() {
  const { data, loading, act, error } = useAsync(service.get);

  const update = (id) => {
    return act(id);
  };

  return {
    recommendation: data,
    errorRecommendation: error,
    loadingRecommendation: loading,
    getRecommendation: act,
    updateRecommendation: update
  };
}
