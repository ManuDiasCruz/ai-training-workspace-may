import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import CreateNewRecommendation from "./CreateNewRecommendation";

describe("CreateNewRecommendation", () => {
  it("submits a recommendation and clears both inputs after success", async () => {
    const onCreateNewRecommendation = jest.fn().mockResolvedValue(undefined);

    render(
      <CreateNewRecommendation
        onCreateNewRecommendation={onCreateNewRecommendation}
      />
    );

    fireEvent.change(screen.getByLabelText("Recommendation name"), {
      target: { value: "A favorite song" }
    });
    fireEvent.change(screen.getByLabelText("YouTube link"), {
      target: { value: "https://youtu.be/abcdefghijk" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Create recommendation" }));

    await waitFor(() => {
      expect(onCreateNewRecommendation).toHaveBeenCalledWith({
        name: "A favorite song",
        link: "https://youtu.be/abcdefghijk"
      });
      expect(screen.getByLabelText("Recommendation name")).toHaveValue("");
      expect(screen.getByLabelText("YouTube link")).toHaveValue("");
    });
  });

  it("disables the form while a recommendation is being created", () => {
    render(<CreateNewRecommendation disabled />);

    expect(screen.getByLabelText("Recommendation name")).toBeDisabled();
    expect(screen.getByLabelText("YouTube link")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Create recommendation" })).toBeDisabled();
  });
});
