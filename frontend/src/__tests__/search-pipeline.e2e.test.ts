import { test, expect } from '@playwright/test'

test.describe('Search Pipeline E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the query service API responses
    await page.route('**/search_pipeline', async (route) => {
      const request = route.request()
      const body = request.postDataJSON()
      
      // Simulate a successful search response
      const mockResponse = {
        query: body.q,
        parse: {
          beds: 3,
          max_price: 600000,
          confidence: 0.95,
          neighborhoods: [],
          keywords: []
        },
        listings: [
          {
            id: 'listing-1',
            price: 575000,
            beds: 3,
            baths: 2.5,
            location: { lat: 39.7392, lon: -104.9903 },
            address: '123 Test St',
            city: 'Denver',
            neighborhood: 'Downtown',
            property_type: 'house',
            title: 'Beautiful 3BR House in Denver',
            description: 'Modern home with great amenities',
            amenities: ['parking', 'garden'],
            images: [],
            date_added: '2024-01-01T12:00:00Z',
            score: 0.92
          },
          {
            id: 'listing-2', 
            price: 585000,
            beds: 3,
            baths: 2,
            location: { lat: 39.7505, lon: -104.9905 },
            address: '456 Demo Ave',
            city: 'Denver',
            neighborhood: 'Capitol Hill',
            property_type: 'house',
            title: 'Charming 3BR House Near Downtown',
            description: 'Historic home with modern updates',
            amenities: ['parking', 'fireplace'],
            images: [],
            date_added: '2024-01-02T12:00:00Z',
            score: 0.88
          }
        ],
        total: 2,
        limit: 10,
        parse_time_ms: 15.2,
        search_time_ms: 32.8,
        total_time_ms: 48.0
      }
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      })
    })

    // Mock auth endpoints
    await page.route('**/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          user: { id: 1, email: 'test@example.com' }
        })
      })
    })

    await page.route('**/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          email: 'test@example.com'
        })
      })
    })
  })

  test('user can search for properties and see results on map', async ({ page }) => {
    // Navigate to the application
    await page.goto('/')

    // Login first
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for the main interface to load
    await expect(page.locator('text=OrbitAgents Chat')).toBeVisible()

    // Type the search query
    const searchInput = page.locator('input[placeholder*="Ask me anything"]')
    await searchInput.fill('3 bed under $600k')

    // Submit the search
    await page.click('button[type="submit"]')

    // Wait for the search to process
    await expect(page.locator('text=Searching properties...')).toBeVisible()

    // Verify the assistant response appears
    await expect(page.locator('text*=I understood you\'re looking for')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('text*=3 bedroom')).toBeVisible()
    await expect(page.locator('text*=under $600,000')).toBeVisible()
    await expect(page.locator('text*=I found 2 matching properties')).toBeVisible()

    // Verify search results are displayed
    await expect(page.locator('text=Search Results')).toBeVisible()
    await expect(page.locator('text=Beautiful 3BR House in Denver')).toBeVisible()
    await expect(page.locator('text=Charming 3BR House Near Downtown')).toBeVisible()

    // Verify property details are shown
    await expect(page.locator('text=$575,000')).toBeVisible()
    await expect(page.locator('text=$585,000')).toBeVisible()
    await expect(page.locator('text=3 bed')).toBeVisible()
    await expect(page.locator('text=2.5 bath')).toBeVisible()

    // Wait for map to load and markers to appear
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000) // Allow time for map markers to render

    // Verify map markers are present
    const mapContainer = page.locator('[class*="mapboxgl-map"]')
    await expect(mapContainer).toBeVisible()

    // Check for property markers on the map
    const markers = page.locator('.property-marker')
    await expect(markers).toHaveCount(2)

    // Test clicking on a map marker to open popup
    await markers.first().click()
    await expect(page.locator('text=Beautiful 3BR House in Denver')).toBeVisible()
    await expect(page.locator('text=123 Test St')).toBeVisible()
  })

  test('user sees helpful error message for failed search', async ({ page }) => {
    // Mock API error response
    await page.route('**/search_pipeline', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'service_error',
          message: 'Search service temporarily unavailable'
        })
      })
    })

    await page.goto('/')

    // Login
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Search with error
    const searchInput = page.locator('input[placeholder*="Ask me anything"]')
    await searchInput.fill('test search')
    await page.click('button[type="submit"]')

    // Verify error message appears
    await expect(page.locator('text*=I encountered an error while searching')).toBeVisible()
    await expect(page.locator('text*=Please try rephrasing your query')).toBeVisible()
  })

  test('user can perform multiple searches', async ({ page }) => {
    await page.goto('/')

    // Login
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')

    // First search
    let searchInput = page.locator('input[placeholder*="Ask me anything"]')
    await searchInput.fill('3 bed under $600k')
    await page.click('button[type="submit"]')
    await expect(page.locator('text*=I found 2 matching properties')).toBeVisible()

    // Second search with different criteria
    searchInput = page.locator('input[placeholder*="Ask me anything"]')
    await searchInput.fill('2 bed apartment downtown')
    await page.click('button[type="submit"]')
    
    // Verify new search results replace old ones
    await expect(page.locator('text*=I understood you\'re looking for')).toBeVisible()
    
    // Verify map markers are updated (should still be 2 for our mock)
    const markers = page.locator('.property-marker')
    await expect(markers).toHaveCount(2)
  })
})

// Additional test configuration
test.afterEach(async ({ page }) => {
  // Clean up any test artifacts
  await page.close()
}) 