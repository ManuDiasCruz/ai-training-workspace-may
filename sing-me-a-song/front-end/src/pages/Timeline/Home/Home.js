import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";

import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, listRecommendations, error } = useRecommendations();
  const { loadingCreatingRecommendation, createRecommendation, creatingRecommendationError } = useCreateRecommendation();

  const handleCreateRecommendation = async (recommendation) => {
    try {
      await createRecommendation({
      name: recommendation.name,
      youtubeLink: recommendation.link,
    });

      listRecommendations().catch(() => {});
      return true;
    } catch { return false; }
  };

  if (loadingRecommendations && !recommendations) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <CreateNewRecommendation disabled={loadingCreatingRecommendation} onCreateNewRecommendation={handleCreateRecommendation} />
      {creatingRecommendationError && <p role="alert">{creatingRecommendationError.response?.status === 409 ? "A song with this name already exists." : creatingRecommendationError.response?.status === 422 ? "Enter a song name and a valid YouTube video link." : "Could not save the song. Please try again."}</p>}
      {error && <p role="alert">Could not load recommendations. <button onClick={() => listRecommendations().catch(() => {})}>Retry</button></p>}
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
        !error && recommendations?.length === 0 && (
          <div>No recommendations yet! Create your own :)</div>
        )
      }
    </>
  )
}
