import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
} from '@testing-library/react';
import { useSearch } from '../hooks/useSearch';
import { SearchProvider } from '../contexts/SearchContext';
import ChatPanel from '../components/Layout/ChatPanel';

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { email: 'fixture@example.test' },
    logout: jest.fn(),
  }),
}));
const response = (q: string, title: string, total = 1) => ({
  query: q,
  listings: total
    ? [
        {
          id: title,
          title,
          address: 'Fixture address',
          city: 'Denver',
          price: 1200,
          beds: 2,
          baths: 1,
          location: { lat: 39.7, lon: -104.9 },
          property_type: 'apartment',
          amenities: [],
          images: [],
          date_added: '2026-10-14',
        },
      ]
    : [],
  total,
  limit: 20,
  parse_time_ms: 1,
  search_time_ms: 2,
  total_time_ms: 3,
});
const ok = (data: unknown) =>
  ({ ok: true, json: async () => data }) as Response;
beforeEach(() => {
  jest.clearAllMocks();
  Element.prototype.scrollIntoView = jest.fn();
});

test('search sends actual criteria and shows only service listings, with no invented property', async () => {
  const fetchMock = jest
    .mocked(fetch)
    .mockResolvedValue(ok(response('2 beds', 'Returned by index')));
  const { result } = renderHook(() => useSearch());
  await act(async () => {
    await result.current.search(' 2 beds ');
  });
  expect(fetchMock).toHaveBeenCalledWith(
    '/api/query/search_pipeline',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        q: '2 beds',
        limit: 20,
        include_parse_details: true,
      }),
    })
  );
  expect(result.current.results.map((x) => x.title)).toEqual([
    'Returned by index',
  ]);
});

test('provider outage clears stale listings and rejects instead of claiming zero matches', async () => {
  jest
    .mocked(fetch)
    .mockResolvedValueOnce(ok(response('first', 'Old result')))
    .mockResolvedValueOnce({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'Index offline' }),
    } as Response);
  const { result } = renderHook(() => useSearch());
  await act(async () => {
    await result.current.search('first');
  });
  await act(async () => {
    await expect(result.current.search('second')).rejects.toThrow(
      'Index offline'
    );
  });
  expect(result.current.results).toEqual([]);
  expect(result.current.error).toBe('Index offline');
  expect(result.current.isLoading).toBe(false);
});

test('malformed provider data is an error, not a completed search', async () => {
  jest.mocked(fetch).mockResolvedValue(ok({ listings: [{}], total: 1 }));
  const { result } = renderHook(() => useSearch());
  await act(async () => {
    await expect(result.current.search('Denver')).rejects.toThrow(
      'invalid listing data'
    );
  });
});

test('late response cannot overwrite a newer search, and clear invalidates requests', async () => {
  let finish!: (value: Response) => void;
  jest
    .mocked(fetch)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        })
    )
    .mockResolvedValueOnce(ok(response('new', 'Latest result')));
  const { result } = renderHook(() => useSearch());
  let old!: Promise<unknown>;
  act(() => {
    old = result.current.search('old').catch((error) => error);
  });
  await act(async () => {
    await result.current.search('new');
  });
  await act(async () => {
    finish(ok(response('old', 'Stale result')));
    await old;
  });
  expect(result.current.results[0].title).toBe('Latest result');
  act(() => result.current.clearSearch());
  expect(result.current.results).toEqual([]);
  expect(result.current.query).toBe('');
});

test('chat reports the returned search immediately instead of stale context from the last render', async () => {
  jest
    .mocked(fetch)
    .mockResolvedValueOnce(ok(response('Denver', 'Current result', 1)))
    .mockResolvedValueOnce(ok(response('empty', '', 0)));
  render(
    <SearchProvider>
      <ChatPanel />
    </SearchProvider>
  );
  fireEvent.change(screen.getByLabelText('Property search'), {
    target: { value: 'Denver' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Search properties' }));
  expect(
    await screen.findByText('Found 1 matching properties. Showing 1 results.')
  ).toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByLabelText('Property search')).not.toBeDisabled()
  );
  fireEvent.change(screen.getByLabelText('Property search'), {
    target: { value: 'empty' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Search properties' }));
  expect(
    await screen.findByText('Found 0 matching properties. Showing 0 results.')
  ).toBeInTheDocument();
  expect(screen.queryByText('Current result')).not.toBeInTheDocument();
});
