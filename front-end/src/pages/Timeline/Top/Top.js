import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, errorLoadingRecommendations, listRecommendations } = useTopRecommendations();

  if (errorLoadingRecommendations && !recommendations) {
    return (
      <div role="alert">
        Unable to load top recommendations. <button onClick={() => listRecommendations().catch(() => undefined)}>Try again</button>
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
            onUpvote={() => listRecommendations().catch(() => undefined)}
            onDownvote={() => listRecommendations().catch(() => undefined)}
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
