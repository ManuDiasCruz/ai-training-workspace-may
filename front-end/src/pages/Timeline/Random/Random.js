import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, recommendationError, getRecommendation } = useRecommendation();

  const handleUpdate = () => {
    return getRecommendation().catch(() => undefined);
  }

  if (recommendationError) {
    return (
      <div role="alert">
        No recommendation is available right now.{' '}
        <button onClick={() => getRecommendation().catch(() => undefined)}>Retry</button>
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
