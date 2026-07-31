import styled from "styled-components";

// Without this the pages render "Loading..." forever whenever the API is
// unreachable, because they only ever check for the absence of data.
export default function LoadError({ error }) {
  const status = error?.response?.status;

  return (
    <Container data-identifier="load-error">
      <strong>Could not reach the Sing me a Song API.</strong>
      <span>
        {status
          ? `The server answered with status ${status}.`
          : `No response from ${process.env.REACT_APP_API_BASE_URL || "http://localhost:5000"}.`}
      </span>
      <span>
        Check that the back-end is running and that REACT_APP_API_BASE_URL
        points at it, then reload the page.
      </span>
    </Container>
  );
}

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 15px;
  border: 1px solid #e90000;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.4;
`;
