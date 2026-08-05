import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Top() {
  const { recommendations, loadingRecommendations, recommendationsError, listRecommendations } = useTopRecommendations();

  if (loadingRecommendations && !recommendations) {
    return <div>Loading...</div>;
  }

  if (recommendationsError && !recommendations) {
    return <div role="alert">Could not load top recommendations. <button onClick={() => listRecommendations().catch(() => {})}>Try again</button></div>;
  }

  return (
    <>
      {recommendationsError && recommendations && <div role="alert">Could not refresh top recommendations. <button onClick={() => listRecommendations().catch(() => {})}>Try again</button></div>}
      {
        (recommendations || []).map(recommendation => (
          <Recommendation
            key={recommendation.id}
            {...recommendation}
            onUpvote={() => listRecommendations()}
            onDownvote={() => listRecommendations()}
          />
        ))
      }

      {
        recommendations && recommendations.length === 0 && (
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
