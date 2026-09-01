import useRecommendation from "../../../hooks/api/useRecommendation";

import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, updateRecommendation, getRecommendation, loadingRecommendation, error } = useRecommendation();

  const handleUpdate = async () => {
    try { await updateRecommendation(recommendation.id); }
    catch (failure) {
      if (failure.response?.status === 404) await getRecommendation().catch(() => {});
    }
  }

  if (loadingRecommendation && !recommendation) {
    return <div>Loading...</div>;
  }

  if (error?.response?.status === 404) return <div>No recommendations yet! Create your own :)</div>;
  if (error) return <p role="alert">Could not load a recommendation. <button onClick={() => getRecommendation().catch(() => {})}>Retry</button></p>;
  if (!recommendation) return null;

  return (
    <>
    <Recommendation
      {...recommendation}
      onUpvote={handleUpdate}
      onDownvote={handleUpdate}
    />
    <button disabled={loadingRecommendation} onClick={() => getRecommendation().catch(() => {})}>Another song</button>
    </>
  );
}
