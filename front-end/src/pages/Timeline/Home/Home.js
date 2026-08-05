import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";

import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, recommendationsError, listRecommendations } = useRecommendations();
  const { loadingCreatingRecommendation, createRecommendation, creatingRecommendationError } = useCreateRecommendation();

  const handleCreateRecommendation = async (recommendation) => {
    try {
      await createRecommendation({
        name: recommendation.name,
        youtubeLink: recommendation.link,
      });
      await listRecommendations();
      return true;
    } catch {
      return false;
    }
  };

  if (loadingRecommendations && !recommendations) {
    return <div>Loading...</div>;
  }

  if (recommendationsError && !recommendations) {
    return <div role="alert">Could not load recommendations. <button onClick={() => listRecommendations().catch(() => {})}>Try again</button></div>;
  }

  return (
    <>
      <CreateNewRecommendation disabled={loadingCreatingRecommendation} onCreateNewRecommendation={handleCreateRecommendation} />
      {creatingRecommendationError && <div role="alert">Could not create recommendation. Check the name and HTTPS YouTube link.</div>}
      {recommendationsError && recommendations && <div role="alert">Could not refresh recommendations. <button onClick={() => listRecommendations().catch(() => {})}>Try again</button></div>}
      {
        (recommendations || []).map(recommendation => (
          <Recommendation
            key={recommendation.id}
            {...recommendation}
            onUpvote={() => listRecommendations()}
            onDownvote={() => listRecommendations()}
          />
        ))
      }

      {
        recommendations && recommendations.length === 0 && (
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
