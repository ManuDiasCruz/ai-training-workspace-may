import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, loadingRecommendation, recommendationError, getRecommendation, updateRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  if (recommendationError && (!recommendation || recommendationError.response?.status === 404)) {
    const empty = recommendationError.response?.status === 404;
    return <div role="alert">{empty ? "No recommendations yet! Create one on the home page." : "Could not load a random recommendation."} <button onClick={() => getRecommendation()}>Try again</button></div>;
  }
  if (!recommendation || loadingRecommendation) {
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
