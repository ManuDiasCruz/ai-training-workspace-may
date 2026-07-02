import { useState } from "react";
import styled from "styled-components";

import { IoReturnUpForwardOutline } from "react-icons/io5";

export default function CreateNewRecommendation({ onCreateNewRecommendation = () => 0, disabled = false }) {
  const [name, setName] = useState("");
  const [link, setLink] = useState("");

  const handleCreateRecommendation = async (event) => {
    event.preventDefault();
    const created = await onCreateNewRecommendation({
      name,
      link
    });

    if (created) {
      setLink("");
      setName("");
    }
  }
  
  return (
    <Container onSubmit={handleCreateRecommendation}>
      <Input type="text" name="name" placeholder="Name" value={name} onChange={e => setName(e.target.value)} disabled={disabled} required />
      <Input type="url" name="youtubeLink" placeholder="https://youtu.be/..." value={link} onChange={e => setLink(e.target.value)} disabled={disabled} required />
      <Button type="submit" disabled={disabled} aria-label="Create recommendation">
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
