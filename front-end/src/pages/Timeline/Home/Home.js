import { useEffect } from "react";

import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";

import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const {
    recommendations,
    errorLoadingRecommendations,
    listRecommendations
  } = useRecommendations();
  const { loadingCreatingRecommendation, createRecommendation, creatingRecommendationError } = useCreateRecommendation();

  const handleCreateRecommendation = async (recommendation) => {
    try {
      await createRecommendation({
        name: recommendation.name,
        youtubeLink: recommendation.link,
      });

      await listRecommendations();
    } catch (_error) {
      // Errors are exposed by the hooks and rendered below.
    }
  };

  useEffect(() => {
    if (creatingRecommendationError) {
      alert(creatingRecommendationError.response?.data?.message || "Error creating recommendation!");
    }
  }, [creatingRecommendationError]);

  if (!recommendations && !errorLoadingRecommendations) {
    return <div>Loading...</div>;
  }

  if (errorLoadingRecommendations && !recommendations) {
    return <div>Could not load recommendations. Check the API connection and try again.</div>;
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
