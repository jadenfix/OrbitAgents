import { act, fireEvent, render, screen } from '@testing-library/react';
import MapPanel from '../components/Layout/MapPanel';
import { SearchContext } from '../contexts/useSearchContext';
import { PropertyListing } from '../types/search';

const mockEvents: Record<string, () => void> = {};
const mockMap = {
  addControl: jest.fn(),
  on: jest.fn((event: string, callback: () => void) => {
    mockEvents[event] = callback;
  }),
  remove: jest.fn(),
  resize: jest.fn(),
  fitBounds: jest.fn(),
  flyTo: jest.fn(),
};
const mockMarkers: Array<{ remove: jest.Mock }> = [];
const mockMarkerConstructor = jest.fn(() => {
  if (mockMarkers.length > 20) throw new Error('Unbounded marker recreation');
  const marker = {
    setLngLat: jest.fn().mockReturnThis(),
    setPopup: jest.fn().mockReturnThis(),
    addTo: jest.fn().mockReturnThis(),
    remove: jest.fn(),
  };
  mockMarkers.push(marker);
  return marker;
});
jest.mock('../components/Layout/mapboxConfig', () => ({
  MAPBOX_TOKEN: 'explicit-test-fixture',
}));
jest.mock('mapbox-gl/dist/mapbox-gl.css', () => ({}));
jest.mock('mapbox-gl', () => ({
  __esModule: true,
  default: {
    Map: jest.fn(() => mockMap),
    Marker: function Marker() {
      return mockMarkerConstructor();
    },
    Popup: jest.fn(() => ({ setHTML: jest.fn().mockReturnThis() })),
    LngLatBounds: jest.fn(() => ({ extend: jest.fn().mockReturnThis() })),
    NavigationControl: jest.fn(),
    FullscreenControl: jest.fn(),
    ScaleControl: jest.fn(),
  },
}));
const listing = (id: string, beds: number, price: number): PropertyListing => ({
  id,
  beds,
  price,
  baths: 1,
  title: 'Fixture listing',
  address: 'Fixture address',
  city: 'Denver',
  property_type: 'apartment',
  amenities: [],
  images: [],
  date_added: '2026-10-13',
  location: { lat: 39.7, lon: -104.9 },
});
const view = (results: PropertyListing[]) => (
  <SearchContext.Provider
    value={{
      query: '',
      results,
      total: results.length,
      isLoading: false,
      search: async () => {},
      clearSearch: () => {},
    }}
  >
    <MapPanel />
  </SearchContext.Provider>
);
beforeEach(() => {
  jest.clearAllMocks();
  mockMarkers.length = 0;
  for (const event of Object.keys(mockEvents)) delete mockEvents[event];
});
test('loaded map creates a bounded marker set, updates filters and cleans resources', () => {
  const results = [listing('one', 1, 1000), listing('two', 2, 2000)];
  const mounted = render(view(results));
  act(() => mockEvents.load());
  expect(mockMarkerConstructor).toHaveBeenCalledTimes(3);
  const originalProperties = mockMarkers.slice(1);
  mounted.rerender(view(results));
  expect(mockMarkerConstructor).toHaveBeenCalledTimes(3);
  fireEvent.click(screen.getByRole('button', { name: '2' }));
  originalProperties.forEach((marker) =>
    expect(marker.remove).toHaveBeenCalledTimes(1)
  );
  expect(mockMarkerConstructor).toHaveBeenCalledTimes(4);
  expect(mockMap.flyTo).toHaveBeenCalledWith(
    expect.objectContaining({ center: [-104.9, 39.7] })
  );
  const filteredMarker = mockMarkers[3];
  mounted.rerender(view([]));
  expect(filteredMarker.remove).toHaveBeenCalledTimes(1);
  expect(mockMarkerConstructor).toHaveBeenCalledTimes(4);
  mounted.rerender(view(results));
  const finalProperties = mockMarkers.slice(4);
  expect(finalProperties).toHaveLength(2);
  mounted.unmount();
  finalProperties.forEach((marker) =>
    expect(marker.remove).toHaveBeenCalledTimes(1)
  );
  expect(mockMap.remove).toHaveBeenCalledTimes(1);
});
