import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, recommendationError, updateRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  if (recommendationError?.response?.status === 404) {
    return <div>No recommendations yet! Create your own :)</div>;
  }

  if (recommendationError) {
    return <div role="alert">Could not load a recommendation. Please try again.</div>;
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
