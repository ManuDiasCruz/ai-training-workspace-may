import { useEffect } from "react";

import useRecommendations from "../../../hooks/api/useRecommendations";
import useCreateRecommendation from "../../../hooks/api/useCreateRecommendation";

import CreateNewRecommendation from "../../../components/CreateNewRecommendation";
import Recommendation from "../../../components/Recommendation";

export default function Home() {
  const { recommendations, recommendationsError, listRecommendations } = useRecommendations();
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

  useEffect(() => {
    if (creatingRecommendationError) {
      alert("Error creating recommendation!");
    }
  }, [creatingRecommendationError]);

  if (recommendationsError) {
    return (
      <div role="alert">
        Could not load recommendations.{' '}
        <button onClick={() => listRecommendations().catch(() => undefined)}>Retry</button>
      </div>
    );
  }

  if (!recommendations) {
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
