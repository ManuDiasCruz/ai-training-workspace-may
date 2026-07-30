import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, recommendationError, updateRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  // The API answers 404 when there is nothing to pick from. Without this the
  // page stayed on "Loading..." forever, because `recommendation` never
  // becomes truthy after a failed request.
  if (!recommendation && recommendationError) {
    return <div>No recommendations yet! Create your own :)</div>;
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
