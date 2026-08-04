import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";

import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, recommendationsError, listRecommendations } = useRecommendations();
  const { loadingCreatingRecommendation, createRecommendation, creatingRecommendationError } = useCreateRecommendation();

  const handleCreateRecommendation = async (recommendation) => {
    const result = await createRecommendation({
      name: recommendation.name,
      youtubeLink: recommendation.link,
    });
    if (result.ok) {
      await listRecommendations();
      return true;
    }
    return false;
  };

  if (!recommendations && recommendationsError) {
    return <div role="alert">Could not load recommendations. <button onClick={listRecommendations}>Try again</button></div>;
  }
  if ((loadingRecommendations && !recommendations) || !recommendations) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <CreateNewRecommendation disabled={loadingCreatingRecommendation} onCreateNewRecommendation={handleCreateRecommendation} />
      {creatingRecommendationError && <div role="alert">Could not create that recommendation. Check the YouTube URL and choose a unique name.</div>}
      {
        recommendations.map(recommendation => (
          <Recommendation
            key={recommendation.id}
            {...recommendation}
            onUpvote={() => listRecommendations()}
            onDownvote={() => listRecommendations()}
          />
        ))
      }

      {
        recommendations.length === 0 && (
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
