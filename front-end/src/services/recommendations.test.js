import api from "./api";
import { create, downvote, get, list, listTop, upvote } from "./recommendations";

jest.mock("./api", () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockResolvedValue({ data: [] });
  api.post.mockResolvedValue({ data: undefined });
});

test("uses the recommendation collection endpoints", async () => {
  await list();
  await listTop();
  await get();
  await get(42);

  expect(api.get.mock.calls).toEqual([
    ["/recommendations"],
    ["/recommendations/top/10"],
    ["/recommendations/random"],
    ["/recommendations/42"],
  ]);
});

test("uses the create and voting endpoints", async () => {
  const recommendation = {
    name: "Example",
    youtubeLink: "https://www.youtube.com/watch?v=12345678901",
  };

  await create(recommendation);
  await upvote(10);
  await downvote(10);

  expect(api.post.mock.calls).toEqual([
    ["/recommendations", recommendation],
    ["/recommendations/10/upvote"],
    ["/recommendations/10/downvote"],
  ]);
});
