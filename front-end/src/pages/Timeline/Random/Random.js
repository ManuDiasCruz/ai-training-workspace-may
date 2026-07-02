import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, errorLoadingRecommendation, getRecommendation, updateRecommendation } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id).catch(() => undefined);
  }

  if (errorLoadingRecommendation && !recommendation) {
    return (
      <div role="alert">
        No recommendation is available. <button onClick={() => getRecommendation().catch(() => undefined)}>Try again</button>
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
