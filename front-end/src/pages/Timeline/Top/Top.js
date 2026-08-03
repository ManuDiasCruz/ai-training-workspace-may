import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import ApiError from "../../../components/ApiError";
import Recommendation from "../../../components/Recommendation";

export default function Top() {
  const { recommendations, loadingRecommendations, recommendationsError, listRecommendations } = useTopRecommendations();

  if (recommendationsError && !recommendations) {
    return <ApiError onRetry={() => listRecommendations()} />;
  }

  if ((loadingRecommendations && !recommendations) || !recommendations) {
    return <div>Loading...</div>;
  }

  return (
    <>
      {
        recommendations.map(recommendation => (
          <Recommendation
            key={recommendation.id}
            {...recommendation}
            onUpvote={() => listRecommendations()}
            onDownvote={() => listRecommendations()}
          />
        ))
      }

      {
        recommendations.length === 0 && (
          <div data-identifier="empty-state">No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
