import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const {
    recommendation,
    recommendationError,
    getRecommendation,
  } = useRecommendation();

  const handleUpdate = () => {
    return getRecommendation();
  }

  if (recommendationError && !recommendation) {
    return (
      <div role="alert">
        Could not load a random recommendation.{" "}
        <button type="button" onClick={() => getRecommendation().catch(() => undefined)}>
          Retry
        </button>
      </div>
    );
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
