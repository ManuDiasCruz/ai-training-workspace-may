import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Home from "./pages/Timeline/Home/Home";
import Random from "./pages/Timeline/Random/Random";
import Recommendation from "./components/Recommendation/Recommendation";
import * as service from "./services/recommendations";
jest.mock("./services/recommendations");
jest.mock("react-player", () => () => <div data-testid="player" />);
beforeEach(() => { jest.resetAllMocks(); service.list.mockResolvedValue([]); });
it("shows an API failure and retries", async () => {
  service.list.mockRejectedValueOnce(new Error("Offline"));
  render(<Home />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not load recommendations");
  fireEvent.click(screen.getByRole("button", {name: "Retry"}));
  expect(await screen.findByText(/No recommendations yet/)).toBeInTheDocument();
});
it("preserves failed submissions and clears only after success", async () => {
  service.create.mockRejectedValueOnce({ response: {status: 409} }).mockResolvedValueOnce("Created");
  render(<Home />);
  await screen.findByText(/No recommendations yet/);
  fireEvent.change(screen.getByLabelText("Name"), {target: {value: "Test song"}});
  fireEvent.change(screen.getByLabelText("YouTube link"), {target: {value: "https://youtu.be/dQw4w9WgXcQ"}});
  fireEvent.click(screen.getByRole("button", {name: "Create recommendation"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("already exists");
  expect(screen.getByLabelText("Name")).toHaveValue("Test song");
  fireEvent.click(screen.getByRole("button", {name: "Create recommendation"}));
  await waitFor(() => expect(screen.getByLabelText("Name")).toHaveValue(""));
  expect(service.create).toHaveBeenCalledWith({name:"Test song", youtubeLink:"https://youtu.be/dQw4w9WgXcQ"});
});
it("does not leave an empty random page loading", async () => {
  service.get.mockRejectedValue({response: {status:404}});
  render(<Random />);
  expect(await screen.findByRole("alert")).toHaveTextContent("No recommendations yet");
  expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
});
it("does not refresh or claim success after a failed vote", async () => {
  service.upvote.mockRejectedValue(new Error("Offline"));
  const refresh = jest.fn();
  render(<Recommendation name="Song" id={1} score={0} youtubeLink="https://youtu.be/dQw4w9WgXcQ" onUpvote={refresh} />);
  fireEvent.click(screen.getByRole("button", {name: "Upvote Song"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not vote");
  expect(refresh).not.toHaveBeenCalled();
});
it("loads another random song when a downvote removes the current song", async () => {
  service.get.mockResolvedValueOnce({id:1,name:"Song",score:-5,youtubeLink:"https://youtu.be/dQw4w9WgXcQ"})
    .mockRejectedValueOnce({response:{status:404}}).mockRejectedValueOnce({response:{status:404}});
  service.downvote.mockResolvedValue("OK");
  render(<Random />);
  fireEvent.click(await screen.findByRole("button", {name: "Downvote Song"}));
  expect(await screen.findByText(/No recommendations yet/)).toBeInTheDocument();
  expect(service.get).toHaveBeenCalledTimes(3);
});
