import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, listRecommendations, recommendationsError } = useTopRecommendations();

  if (recommendationsError && !recommendations) {
    return <div>Could not load recommendations. <button onClick={listRecommendations}>Retry</button></div>;
  }

  if (!recommendations) {
    return <div>{loadingRecommendations ? "Loading..." : "Preparing recommendations..."}</div>;
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
