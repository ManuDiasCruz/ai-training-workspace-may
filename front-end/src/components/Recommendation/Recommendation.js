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
      // The hook stores the error and the effect below reports it.
    }
  };

  const handleDownvote = async () => {
    try {
      await downvoteRecommendation(id);
      await onDownvote();
    } catch (error) {
      // The hook stores the error and the effect below reports it.
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
        <GoArrowUp data-identifier="upvote" size="24px" onClick={handleUpvote} />
        {score}
        <GoArrowDown data-identifier="downvote" size="24px" onClick={handleDownvote} />
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
