import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, loadingRecommendation, recommendationError, getRecommendation } = useRecommendation();

  const handleUpdate = () => {
    return getRecommendation().catch(() => {});
  }

  if (loadingRecommendation && !recommendation) {
    return <div>Loading...</div>;
  }

  if (recommendationError) {
    const empty = recommendationError.response?.status === 404;
    return <div role={empty ? undefined : "alert"}>{empty ? "No recommendations yet! Create one on the home page." : "Could not load a random recommendation."} <button onClick={handleUpdate}>Try again</button></div>;
  }

  if (!recommendation) return null;

  return (
    <Recommendation
      {...recommendation}
      onUpvote={handleUpdate}
      onDownvote={handleUpdate}
    />
  );
}
