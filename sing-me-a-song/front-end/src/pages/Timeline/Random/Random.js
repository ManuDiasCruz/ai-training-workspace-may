import useRecommendation from "../../../hooks/api/useRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Random() {
  const { recommendation, updateRecommendation, getRecommendation, errorRecommendation } = useRecommendation();
  const handleUpdate = async () => {
    const result = await updateRecommendation(recommendation.id);
    if (!result.success && result.error?.response?.status === 404) await getRecommendation();
  };
  if (errorRecommendation) return <div role="alert">
    {errorRecommendation.response?.status === 404 ? "No recommendations yet! Create your own :)" : "Could not load recommendation."}
    <button onClick={() => getRecommendation()}>Try again</button>
  </div>;
  if (!recommendation) return <div>Loading...</div>;
  return <Recommendation {...recommendation} onUpvote={handleUpdate} onDownvote={handleUpdate} />;
}
