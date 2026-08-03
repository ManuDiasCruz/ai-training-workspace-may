import { useState } from "react";
import styled from "styled-components";

import { IoReturnUpForwardOutline } from "react-icons/io5";

export default function CreateNewRecommendation({ onCreateNewRecommendation = () => 0, disabled = false }) {
  const [name, setName] = useState("");
  const [link, setLink] = useState("");

  const handleCreateRecommendation = async (event) => {
    event.preventDefault();

    try {
      await onCreateNewRecommendation({
        name: name.trim(),
        link: link.trim()
      });
      setLink("");
      setName("");
    } catch {
      // The parent keeps the form values and presents the request error.
    }
  }
  
  return (
    <Container onSubmit={handleCreateRecommendation}>
      <Input
        aria-label="Song name"
        type="text"
        placeholder="Name"
        value={name}
        onChange={e => setName(e.target.value)}
        disabled={disabled}
        maxLength={100}
        required
      />
      <Input
        aria-label="YouTube link"
        type="url"
        placeholder="https://youtu.be/..."
        value={link}
        onChange={e => setLink(e.target.value)}
        disabled={disabled}
        maxLength={2048}
        required
      />
      <Button type="submit" aria-label="Add recommendation" disabled={disabled}>
        <IoReturnUpForwardOutline size="24px" color="#fff" />
      </Button>
    </Container>
  );
}

const Container = styled.form`
  display: flex;
  gap: 9px;
  margin-bottom: 15px;
`;

const Input = styled.input`
  background-color: #fff;
  border: none;
  border-radius: 4px;
  padding: 9px 13px;
  color: #141414;
  width: 100%;
  font-family: "Lexend Deca", sans-serif;

  &:disabled {
    opacity: .8;
  }

  &::placeholder {
    color: #c4c4c4;
  }
`;

const Button = styled.button`
  background-color: #e90000;
  border: none;
  border-radius: 4px;
  padding: 9px 13px;
  width: 59px;
  color: #fff;
  cursor: pointer;

  &:disabled {
    opacity: .8;
  }
`;
