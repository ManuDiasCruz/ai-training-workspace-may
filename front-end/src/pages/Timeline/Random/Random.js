import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, recommendationError, getRecommendation, updateRecommendation } = useRecommendation();

  const handleUpdate = async () => {
    const updated = await updateRecommendation(recommendation.id);

    // The recommendation was removed (score dropped below -5): pick another one.
    if (!updated) {
      getRecommendation();
    }
  };

  if (recommendationError?.response?.status === 404) {
    return <div>No recommendations yet! Create your own :)</div>;
  }

  if (recommendationError) {
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
