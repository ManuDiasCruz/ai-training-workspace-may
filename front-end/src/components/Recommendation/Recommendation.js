import styled from "styled-components";
import { useEffect } from "react";

import ReactPlayer from "react-player";
import { GoArrowUp, GoArrowDown } from "react-icons/go";

import useUpvoteRecommendation from "../../hooks/api/useUpvoteRecommendation";
import useDownvoteRecommendation from "../../hooks/api/useDownvoteRecommendation";

export default function Recommendation({ name, youtubeLink, score, id, onUpvote = () => 0, onDownvote = () => 0 }) {
  const { upvoteRecommendation, errorUpvotingRecommendation } = useUpvoteRecommendation();
  const { downvoteRecommendation, errorDownvotingRecommendation } = useDownvoteRecommendation();

  const handleUpvote = async () => {
    try {
      await upvoteRecommendation(id);
      await onUpvote();
    } catch (error) {
      // The hook exposes the request error to the effect below.
    }
  };

  const handleDownvote = async () => {
    try {
      await downvoteRecommendation(id);
      await onDownvote();
    } catch (error) {
      // The hook exposes the request error to the effect below.
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
      <Row>
        <VoteButton type="button" onClick={handleUpvote} aria-label={`Upvote ${name}`} data-identifier="upvote">
          <GoArrowUp size="24px" />
        </VoteButton>
        <span data-identifier="score">{score}</span>
        <VoteButton type="button" onClick={handleDownvote} aria-label={`Downvote ${name}`} data-identifier="downvote">
          <GoArrowDown size="24px" />
        </VoteButton>
      </Row>
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

const VoteButton = styled.button`
  align-items: center;
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  display: flex;
  padding: 0;
`;
