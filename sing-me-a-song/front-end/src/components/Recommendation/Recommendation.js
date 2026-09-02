import styled from "styled-components";

import ReactPlayer from "react-player";
import { GoArrowUp, GoArrowDown } from "react-icons/go";

import useUpvoteRecommendation from "../../hooks/api/useUpvoteRecommendation";
import useDownvoteRecommendation from "../../hooks/api/useDownvoteRecommendation";

export default function Recommendation({ name, youtubeLink, score, id, onUpvote = () => 0, onDownvote = () => 0 }) {
  const { upvoteRecommendation, errorUpvotingRecommendation, loadingUpvoteRecommendations } = useUpvoteRecommendation();
  const { downvoteRecommendation, errorDownvotingRecommendation, loadingDownvoteRecommendations } = useDownvoteRecommendation();
  const pending = loadingUpvoteRecommendations || loadingDownvoteRecommendations;

  const handleUpvote = async () => {
    try { await upvoteRecommendation(id); await onUpvote(); } catch { /* shown below or by the parent */ }
  };

  const handleDownvote = async () => {
    try { await downvoteRecommendation(id); await onDownvote(); } catch { /* shown below or by the parent */ }
  };

  return (
    <Container>
      <Row>{name}</Row>
      <ReactPlayer url={youtubeLink} width="100%" height="300px" controls />
      <Row data-identifier="vote-menu">
        <VoteButton aria-label={`Upvote ${name}`} data-identifier="upvote" disabled={pending} onClick={handleUpvote}><GoArrowUp size="24px" /></VoteButton>
        <span aria-label="Score">{score}</span>
        <VoteButton aria-label={`Downvote ${name}`} data-identifier="downvote" disabled={pending} onClick={handleDownvote}><GoArrowDown size="24px" /></VoteButton>
      </Row>
      {(errorUpvotingRecommendation || errorDownvotingRecommendation) && <p role="alert">Could not save your vote. Please try again.</p>}
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
  color: inherit;
  background: none;
  border: 0;
  padding: 3px;
  cursor: pointer;
  &:disabled { opacity: .5; cursor: wait; }
`;
