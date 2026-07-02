import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, recommendationError, updateRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation().catch(() => {
      // The hook stores the error for the state below.
    });
  }

  if (recommendationError) {
    return <div>No recommendation is available yet. Add a song from the home page first.</div>;
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
