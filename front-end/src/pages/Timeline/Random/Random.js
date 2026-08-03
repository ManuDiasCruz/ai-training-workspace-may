import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const {
    recommendation,
    loadingRecommendation,
    recommendationError,
    updateRecommendation
  } = useRecommendation();

  const handleUpdate = () => {
    updateRecommendation(recommendation.id);
  }

  if (loadingRecommendation && !recommendation) {
    return <div>Loading...</div>;
  }

  // GET /recommendations/random answers 404 on an empty database, and the same
  // happens after the sixth downvote deletes the song being displayed. Without
  // this branch the page stayed on "Loading..." forever.
  if (recommendationError || !recommendation) {
    return (
      <div data-identifier="empty-state">
        No recommendations yet! Create your own :)
      </div>
    );
  }

  return (
    <Recommendation
      {...recommendation}
      onUpvote={handleUpdate}
      onDownvote={handleUpdate}
    />
  );
}
