import { render, screen } from "@testing-library/react";
import Header from "./Header";

test("renders the application header", () => {
  render(<Header />);

  expect(screen.getByText(/sing me a song/i)).toBeTruthy();
});
