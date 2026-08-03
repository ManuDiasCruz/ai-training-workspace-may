import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, updateRecommendation, errorLoadingRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  if (errorLoadingRecommendation && !recommendation) {
    return <div>Could not load a recommendation. Is the API running?</div>;
  }

  if (!recommendation) {
    return <div>Loading...</div>;
  }

  return (
    <Recommendation
      {...recommendation}
      onUpvote={handleUpdate}
      onDownvote={handleUpdate}
    />
  );
}
