import styled from "styled-components";

import ReactPlayer from "react-player";
import { GoArrowUp, GoArrowDown } from "react-icons/go";

import useUpvoteRecommendation from "../../hooks/api/useUpvoteRecommendation";
import useDownvoteRecommendation from "../../hooks/api/useDownvoteRecommendation";

export default function Recommendation({ name, youtubeLink, score, id, onUpvote = () => 0, onDownvote = () => 0 }) {
  const { upvoteRecommendation, loadingUpvoteRecommendations, errorUpvotingRecommendation } = useUpvoteRecommendation();
  const { downvoteRecommendation, loadingDownvoteRecommendations, errorDownvotingRecommendation } = useDownvoteRecommendation();
  const voting = loadingUpvoteRecommendations || loadingDownvoteRecommendations;

  const handleUpvote = async () => {
    const result = await upvoteRecommendation(id);
    if (result.ok) onUpvote();
  };

  const handleDownvote = async () => {
    const result = await downvoteRecommendation(id);
    if (result.ok) onDownvote();
  };

  return (
    <Container>
      <Row>{name}</Row>
      <ReactPlayer url={youtubeLink} width="100%" height="100%" />
      <Row>
        <VoteButton aria-label={`Upvote ${name}`} data-identifier="upvote" onClick={handleUpvote} disabled={voting}><GoArrowUp size="24px" /></VoteButton>
        <span data-identifier="score">{score}</span>
        <VoteButton aria-label={`Downvote ${name}`} data-identifier="downvote" onClick={handleDownvote} disabled={voting}><GoArrowDown size="24px" /></VoteButton>
      </Row>
      {(errorUpvotingRecommendation || errorDownvotingRecommendation) && <Row role="alert">Could not save your vote. Try again.</Row>}
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
`;

const VoteButton = styled.button`
  display: inline-flex;
  padding: 0;
  color: inherit;
  background: transparent;
  border: 0;
  cursor: pointer;
  &:disabled { opacity: .5; cursor: wait; }
`;
