import styled from "styled-components";

import { baseURL } from "../../services/api";

/**
 * Rendered when a list request fails. The pages previously stayed on
 * "Loading..." forever in that case, which made an unreachable or
 * misconfigured API look like an app that simply never finishes loading.
 */
export default function ApiError({ onRetry }) {
  return (
    <Container data-identifier="api-error">
      <strong>Could not reach the API.</strong>
      <span>
        Tried <code>{baseURL}</code>. Check that the back-end is running and
        that REACT_APP_API_BASE_URL points at it.
      </span>
      {onRetry && (
        <RetryButton data-identifier="retry" onClick={onRetry}>
          Try again
        </RetryButton>
      )}
    </Container>
  );
}

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 15px;
  border-radius: 4px;
  background-color: rgba(233, 0, 0, 0.15);
  font-size: 14px;
  font-weight: 300;
  line-height: 1.4;

  code {
    font-family: monospace;
    word-break: break-all;
  }
`;

const RetryButton = styled.button`
  background-color: #e90000;
  border: none;
  border-radius: 4px;
  padding: 7px 14px;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
`;
