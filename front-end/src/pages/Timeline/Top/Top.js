import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Top() {
  const {
    recommendations,
    loadingRecommendations,
    recommendationsError,
    listRecommendations
  } = useTopRecommendations();

  if (loadingRecommendations && !recommendations) {
    return <div>Loading...</div>;
  }

  if (recommendationsError || !recommendations) {
    return <div>Failed to load recommendations.</div>;
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
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
