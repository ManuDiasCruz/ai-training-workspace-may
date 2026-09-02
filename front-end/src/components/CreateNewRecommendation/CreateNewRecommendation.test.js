import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import CreateNewRecommendation from "./CreateNewRecommendation";

describe("CreateNewRecommendation", () => {
  it("submits the API field names and clears the form after success", async () => {
    const onCreateNewRecommendation = jest.fn().mockResolvedValue(true);

    render(
      <CreateNewRecommendation
        onCreateNewRecommendation={onCreateNewRecommendation}
      />
    );

    const nameInput = screen.getByPlaceholderText("Name");
    const linkInput = screen.getByPlaceholderText("https://youtu.be/...");

    fireEvent.change(nameInput, { target: { value: "A song" } });
    fireEvent.change(linkInput, {
      target: { value: "https://youtu.be/dQw4w9WgXcQ" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create recommendation" }));

    await waitFor(() => {
      expect(onCreateNewRecommendation).toHaveBeenCalledWith({
        name: "A song",
        youtubeLink: "https://youtu.be/dQw4w9WgXcQ",
      });
    });

    await waitFor(() => {
      expect(nameInput.value).toBe("");
      expect(linkInput.value).toBe("");
    });
  });
});
