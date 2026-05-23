import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, loadingRecommendation, recommendationError, updateRecommendation } = useRecommendation();

  if (loadingRecommendation && !recommendation) {
    return <div>Loading...</div>;
  }

  if (recommendationError) {
    return <div>No recommendations yet! Create your own :)</div>;
  }

  if (!recommendation) {
    return <div>No recommendations yet! Create your own :)</div>;
  }

  return (
    <Recommendation
      {...recommendation}
      onUpvote={updateRecommendation}
      onDownvote={updateRecommendation}
    />
  );
}
