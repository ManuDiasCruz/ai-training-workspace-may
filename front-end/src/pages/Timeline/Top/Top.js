import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const {
    recommendations,
    errorLoadingRecommendations,
    listRecommendations
  } = useTopRecommendations();

  if (!recommendations && !errorLoadingRecommendations) {
    return <div>Loading...</div>;
  }

  if (errorLoadingRecommendations && !recommendations) {
    return <div>Could not load the top recommendations. Check the API connection and try again.</div>;
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
