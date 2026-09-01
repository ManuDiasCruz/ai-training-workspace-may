import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";
import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, errorRecommendations, listRecommendations } = useRecommendations();
  const { loadingCreatingRecommendation, createRecommendation, creatingRecommendationError } = useCreateRecommendation();
  const handleCreateRecommendation = async ({ name, link }) => {
    const result = await createRecommendation({ name, youtubeLink: link });
    if (result.success) await listRecommendations();
    return result.success;
  };
  const message = creatingRecommendationError?.response?.status === 409
    ? "A recommendation with this name already exists."
    : creatingRecommendationError?.response?.status === 422
    ? "Enter a name and a valid YouTube video URL."
    : "Could not create recommendation. Please try again.";
  return <>
    <CreateNewRecommendation disabled={loadingCreatingRecommendation} onCreateNewRecommendation={handleCreateRecommendation} />
    {creatingRecommendationError && <p role="alert">{message}</p>}
    {errorRecommendations ? <div role="alert">Could not load recommendations. <button onClick={() => listRecommendations()}>Retry</button></div>
      : !recommendations ? <div>Loading...</div> : <>
        {loadingRecommendations && <p role="status">Refreshing...</p>}
        {recommendations.map(recommendation => <Recommendation key={recommendation.id} {...recommendation}
          onUpvote={() => listRecommendations()} onDownvote={() => listRecommendations()} />)}
        {recommendations.length === 0 && <div>No recommendations yet! Create your own :)</div>}
      </>}
  </>;
}
