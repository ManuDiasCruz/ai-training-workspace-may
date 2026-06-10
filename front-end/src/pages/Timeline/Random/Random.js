import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const {
    recommendation,
    loadingRecommendation,
    recommendationError,
    getRecommendation
  } = useRecommendation();

  const handleUpdate = () => {
    getRecommendation();
  }

  if (recommendationError) {
    return <div>No recommendations yet! Create your own :)</div>;
  }

  if (loadingRecommendation || !recommendation) {
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
