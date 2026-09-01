import styled from "styled-components";


import ReactPlayer from "react-player";
import { GoArrowUp, GoArrowDown } from "react-icons/go";

import useUpvoteRecommendation from "../../hooks/api/useUpvoteRecommendation";
import useDownvoteRecommendation from "../../hooks/api/useDownvoteRecommendation";

export default function Recommendation({ name, youtubeLink, score, id, onUpvote = () => 0, onDownvote = () => 0 }) {
  const { upvoteRecommendation, errorUpvotingRecommendation, loadingUpvoteRecommendations } = useUpvoteRecommendation();
  const { downvoteRecommendation, errorDownvotingRecommendation, loadingDownvoteRecommendations } = useDownvoteRecommendation();

  const handleUpvote = async () => {
    const result = await upvoteRecommendation(id);
    if (result.success) onUpvote();
  };

  const handleDownvote = async () => {
    const result = await downvoteRecommendation(id);
    if (result.success) onDownvote();
  };

  const voting = loadingUpvoteRecommendations || loadingDownvoteRecommendations;

  return (
    <Container>
      <Row>{name}</Row>
      <ReactPlayer url={youtubeLink} controls width="100%" height="240px" />
      <Row>
        <VoteButton aria-label={`Upvote ${name}`} disabled={voting} onClick={handleUpvote}><GoArrowUp size="24px" /></VoteButton>
        {score}
        <VoteButton aria-label={`Downvote ${name}`} disabled={voting} onClick={handleDownvote}><GoArrowDown size="24px" /></VoteButton>
      </Row>
      {(errorUpvotingRecommendation || errorDownvotingRecommendation) && <p role="alert">Could not vote. Please try again.</p>}
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
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  &:disabled { opacity: .5; cursor: wait; }
`;
