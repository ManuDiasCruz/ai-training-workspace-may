import { useEffect } from "react";

import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";

import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, loadingRecommendations, listRecommendations, errorLoadingRecommendations } = useRecommendations();
  const { loadingCreatingRecommendation, createRecommendation, creatingRecommendationError } = useCreateRecommendation();

  const handleCreateRecommendation = async (recommendation) => {
    await createRecommendation({
      name: recommendation.name,
      youtubeLink: recommendation.link,
    });

    listRecommendations();
  };

  useEffect(() => {
    if (creatingRecommendationError) {
      alert("Error creating recommendation!");
    }
  }, [creatingRecommendationError]);

  if (errorLoadingRecommendations && !recommendations) {
    return <div>Could not load recommendations. Is the API running?</div>;
  }

  if ((loadingRecommendations && !recommendations) || !recommendations) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <CreateNewRecommendation disabled={loadingCreatingRecommendation} onCreateNewRecommendation={handleCreateRecommendation} />
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
