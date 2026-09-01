import useTopRecommendations from "../../../hooks/api/useTopRecommendations";

import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, listRecommendations, error } = useTopRecommendations();

  if (loadingRecommendations && !recommendations) {
    return <div>Loading...</div>;
  }

  return (
    <>
      {error && <p role="alert">Could not load recommendations. <button onClick={() => listRecommendations().catch(() => {})}>Retry</button></p>}
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
        !error && recommendations?.length === 0 && (
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
