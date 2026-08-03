import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const {
    recommendations,
    loadingRecommendations,
    recommendationsError,
    listRecommendations,
  } = useTopRecommendations();

  if (recommendationsError && !recommendations) {
    return (
      <div role="alert">
        Could not load top recommendations.{" "}
        <button type="button" onClick={() => listRecommendations().catch(() => undefined)}>
          Retry
        </button>
      </div>
    );
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
            onUpvote={listRecommendations}
            onDownvote={listRecommendations}
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
