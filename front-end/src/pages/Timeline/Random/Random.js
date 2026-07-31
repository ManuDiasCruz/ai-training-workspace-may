import useRecommendation from "../../../hooks/api/useRecommendation";

import LoadError from "../../../components/LoadError";
import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, recommendationError, updateRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  if (recommendationError && !recommendation) {
    return <LoadError error={recommendationError} />;
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
