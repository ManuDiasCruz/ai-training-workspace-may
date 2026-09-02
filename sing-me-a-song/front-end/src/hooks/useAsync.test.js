import { act, renderHook, waitFor } from '@testing-library/react';
import useAsync from './useAsync';

test('returns successful mutation results and propagates failures', async () => {
  const failure = new Error('offline');
  const handler = jest.fn().mockResolvedValueOnce({ id: 1 }).mockRejectedValueOnce(failure);
  const { result } = renderHook(() => useAsync(handler, false));
  await act(async () => { expect(await result.current.act()).toEqual({ id: 1 }); });
  await act(async () => { await expect(result.current.act()).rejects.toBe(failure); });
  expect(result.current.error).toBe(failure);
  expect(result.current.loading).toBe(false);
});

test('reports an initial request failure without leaving a loading state', async () => {
  const { result } = renderHook(() => useAsync(() => Promise.reject(new Error('offline'))));
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.error.message).toBe('offline');
});

test('does not overwrite a newer result with an older response', async () => {
  let resolveOld;
  const handler = jest.fn().mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValueOnce('new');
  const { result } = renderHook(() => useAsync(handler, false));
  let oldRequest;
  act(() => { oldRequest = result.current.act(); });
  await act(async () => { await result.current.act(); });
  await act(async () => { resolveOld('old'); await oldRequest; });
  expect(result.current.data).toBe('new');
});
