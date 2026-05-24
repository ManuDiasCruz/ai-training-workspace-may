import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const {
    recommendation,
    loadingRecommendation,
    recommendationError,
    getRecommendation,
    updateRecommendation
  } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  if (loadingRecommendation) {
    return <div>Loading...</div>;
  }

  if (recommendationError || !recommendation) {
    return (
      <div>
        <div>No recommendations available yet.</div>
        <button onClick={() => getRecommendation().catch(() => undefined)}>Try again</button>
      </div>
    );
  }

  return (
    <Recommendation
      {...recommendation}
      onUpvote={handleUpdate}
      onDownvote={handleUpdate}
    />
  );
}
