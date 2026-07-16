import styled from "styled-components";
import { useEffect } from "react";

import ReactPlayer from "react-player";
import { GoArrowUp, GoArrowDown } from "react-icons/go";

import useUpvoteRecommendation from "../../hooks/api/useUpvoteRecommendation";
import useDownvoteRecommendation from "../../hooks/api/useDownvoteRecommendation";

export default function Recommendation({ name, youtubeLink, score, id, onUpvote = () => 0, onDownvote = () => 0 }) {
  const { loadingUpvoteRecommendations, upvoteRecommendation, errorUpvotingRecommendation } = useUpvoteRecommendation();
  const { loadingDownvoteRecommendations, downvoteRecommendation, errorDownvotingRecommendation } = useDownvoteRecommendation();
  const isVoting = loadingUpvoteRecommendations || loadingDownvoteRecommendations;

  const handleUpvote = async () => {
    try {
      await upvoteRecommendation(id);
      await onUpvote();
    } catch {
      // The hooks expose request failures to the UI below.
    }
  };

  const handleDownvote = async () => {
    try {
      await downvoteRecommendation(id);
      await onDownvote();
    } catch {
      // The hooks expose request failures to the UI below.
    }
  };

  useEffect(() => {
    if (errorUpvotingRecommendation) {
      alert("Error upvoting recommendation!");
    }
  }, [errorUpvotingRecommendation]);

  useEffect(() => {
    if (errorDownvotingRecommendation) {
      alert("Error downvoting recommendation!");
    }

  }, [errorDownvotingRecommendation]);

  return (
    <Container>
      <Row>{name}</Row>
      <ReactPlayer url={youtubeLink} width="100%" height="100%" />
      <VoteRow data-identifier="vote-menu">
        <VoteButton data-identifier="upvote" aria-label={`Upvote ${name}`} onClick={handleUpvote} disabled={isVoting}>
          <GoArrowUp size="24px" />
        </VoteButton>
        {score}
        <VoteButton data-identifier="downvote" aria-label={`Downvote ${name}`} onClick={handleDownvote} disabled={isVoting}>
          <GoArrowDown size="24px" />
        </VoteButton>
      </VoteRow>
    </Container>
  );
}

const Container = styled.article`
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px 0;
  background-color: rgba(255, 255, 255, .1);
  border-radius: 4px;
  margin-bottom: 15px;
`;

const Row = styled.div`
  padding: 0 15px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
`;

const VoteRow = styled(Row)`
  cursor: default;
`;

const VoteButton = styled.button`
  align-items: center;
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  display: flex;
  padding: 0;

  &:disabled {
    cursor: wait;
    opacity: .6;
  }
`;
