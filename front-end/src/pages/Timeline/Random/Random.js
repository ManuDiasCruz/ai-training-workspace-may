import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, getRecommendation, recommendationError } = useRecommendation();

  const handleUpdate = () => {
    getRecommendation();
  }

  if (recommendationError && !recommendation) {
    return <div>Could not load a random recommendation. <button onClick={getRecommendation}>Retry</button></div>;
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
