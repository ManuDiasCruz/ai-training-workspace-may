import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import Home from './Home/Home';
import Top from './Top/Top';
import Random from './Random/Random';
import * as songs from '../../services/recommendations';

jest.mock('../../services/recommendations');
jest.mock('react-player', () => () => <div>YouTube player</div>);
const song = { id: 1, name: 'A test song', youtubeLink: 'https://youtu.be/qmUQr3zrqXM', score: 0 };
beforeEach(() => { jest.resetAllMocks(); songs.list.mockResolvedValue([]); });

test.each([[Home, 'list'], [Top, 'listTop']])('offers a working retry when a list request fails', async (Page, method) => {
  songs[method].mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce([]);
  render(<Page />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not load recommendations');
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  expect(await screen.findByText(/No recommendations yet/)).toBeInTheDocument();
});

test('preserves form input after a rejected save and only clears after success', async () => {
  songs.create.mockRejectedValueOnce({ response: { status: 409 } }).mockResolvedValueOnce(song);
  render(<Home />);
  const name = await screen.findByLabelText('Song name');
  const link = screen.getByLabelText('YouTube link');
  fireEvent.change(name, { target: { value: song.name } });
  fireEvent.change(link, { target: { value: song.youtubeLink } });
  fireEvent.click(screen.getByRole('button', { name: 'Add recommendation' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('already exists');
  expect(name).toHaveValue(song.name);
  expect(link).toHaveValue(song.youtubeLink);
  expect(songs.list).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Add recommendation' }));
  await waitFor(() => expect(name).toHaveValue(''));
  expect(link).toHaveValue('');
  expect(songs.create).toHaveBeenLastCalledWith({ name: song.name, youtubeLink: song.youtubeLink });
});

test('a failed vote displays an error without pretending to refresh successfully', async () => {
  songs.list.mockResolvedValue([song]);
  songs.upvote.mockRejectedValue(new Error('offline'));
  render(<Home />);
  fireEvent.click(await screen.findByRole('button', { name: `Upvote ${song.name}` }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not save your vote');
  expect(songs.list).toHaveBeenCalledTimes(1);
  expect(screen.getByLabelText('Score')).toHaveTextContent('0');
});

test('an empty random feed is not an infinite loading screen', async () => {
  songs.get.mockRejectedValue({ response: { status: 404 } });
  render(<Random />);
  expect(await screen.findByText(/No recommendations yet/)).toBeInTheDocument();
});

test('removes a deleted random recommendation and falls back to the empty state', async () => {
  songs.get.mockResolvedValueOnce(song).mockRejectedValue({ response: { status: 404 } });
  songs.downvote.mockResolvedValue('OK');
  render(<Random />);
  fireEvent.click(await screen.findByRole('button', { name: `Downvote ${song.name}` }));
  expect(await screen.findByText(/No recommendations yet/)).toBeInTheDocument();
  expect(screen.queryByText(song.name)).not.toBeInTheDocument();
  expect(songs.get).toHaveBeenCalledTimes(3);
});
