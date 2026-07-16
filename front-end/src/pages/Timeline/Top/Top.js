import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Top() {
  const { recommendations, recommendationsError, listRecommendations } = useTopRecommendations();

  if (recommendationsError) {
    return (
      <div role="alert">
        Could not load the top recommendations.{' '}
        <button onClick={() => listRecommendations().catch(() => undefined)}>Retry</button>
      </div>
    );
  }

  if (!recommendations) {
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
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
