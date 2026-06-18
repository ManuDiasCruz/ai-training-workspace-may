import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const {
    recommendation,
    errorLoadingRecommendation,
    updateRecommendation
  } = useRecommendation();

  const handleUpdate = async () => {
    try {
      await updateRecommendation(recommendation.id);
    } catch (error) {
      if (error.response?.status === 404) {
        await updateRecommendation();
      }
    }
  }

  if (!recommendation && !errorLoadingRecommendation) {
    return <div>Loading...</div>;
  }

  if (errorLoadingRecommendation && !recommendation) {
    return <div>No recommendation is available yet.</div>;
  }

  return (
    <Recommendation
      {...recommendation}
      onUpvote={handleUpdate}
      onDownvote={handleUpdate}
    />
  );
}
