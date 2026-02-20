#!/usr/bin/env python3
"""
STAC Harvester - Enriches location data with Sentinel-2 satellite imagery metadata.

Connects to the public Earth Search API to fetch the clearest satellite image
for each location within the last 12 months.
"""

import json
from datetime import datetime, timedelta
from pystac_client import Client

# Configuration
STAC_API_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"
INPUT_FILE = "global_atlas_diagnostic.json"
OUTPUT_FILE = "global_atlas_satellite_enriched.json"
BBOX_OFFSET = 0.01  # degrees
TIME_WINDOW_MONTHS = 12


def create_bbox(lat: float, lon: float, offset: float = BBOX_OFFSET) -> list:
    """Create a bounding box around a lat/lon point."""
    return [
        lon - offset,  # west
        lat - offset,  # south
        lon + offset,  # east
        lat + offset   # north
    ]


def get_time_range(months: int = TIME_WINDOW_MONTHS) -> str:
    """Get ISO date range string for the last N months."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)
    return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"


def fetch_satellite_preview(client: Client, lat: float, lon: float, location_name: str) -> dict | None:
    """
    Fetch the clearest satellite image metadata for a location.
    
    Returns satellite_preview dict or None if no image found.
    """
    bbox = create_bbox(lat, lon)
    time_range = get_time_range()
    
    try:
        search = client.search(
            collections=[COLLECTION],
            bbox=bbox,
            datetime=time_range,
            sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
            max_items=1
        )
        
        items = list(search.items())
        
        if not items:
            print(f"  ⚠ No image found for {location_name}")
            return None
        
        item = items[0]
        
        # Extract thumbnail URL
        thumbnail_url = None
        if 'thumbnail' in item.assets:
            thumbnail_url = item.assets['thumbnail'].href
        elif 'visual' in item.assets:
            thumbnail_url = item.assets['visual'].href
        
        cloud_cover = item.properties.get('eo:cloud_cover', None)
        capture_date = item.properties.get('datetime', None)
        
        print(f"  ✓ Found image for {location_name}: {cloud_cover:.1f}% clouds")
        
        return {
            "thumbnail_url": thumbnail_url,
            "capture_date": capture_date,
            "cloud_cover": cloud_cover,
            "satellite_id": item.id
        }
        
    except Exception as e:
        print(f"  ✗ Error for {location_name}: {str(e)}")
        return None


def main():
    """Main execution - process all locations."""
    print("=" * 60)
    print("STAC Satellite Harvester")
    print("=" * 60)
    
    # Load input data
    print(f"\nLoading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        locations = json.load(f)
    
    print(f"Found {len(locations)} locations to process")
    
    # Connect to STAC API
    print(f"\nConnecting to {STAC_API_URL}...")
    client = Client.open(STAC_API_URL)
    print("Connected successfully!")
    
    # Process each location
    print(f"\nHarvesting satellite imagery (last {TIME_WINDOW_MONTHS} months)...\n")
    
    success_count = 0
    fail_count = 0
    
    for i, location in enumerate(locations, 1):
        lat = location['location']['lat']
        lon = location['location']['lon']
        name = location.get('target', {}).get('name', f'Location {i}')
        
        print(f"[{i}/{len(locations)}] Processing {name} ({lat:.4f}, {lon:.4f})")
        
        satellite_preview = fetch_satellite_preview(client, lat, lon, name)
        location['satellite_preview'] = satellite_preview
        
        if satellite_preview:
            success_count += 1
        else:
            fail_count += 1
    
    # Save enriched data
    print(f"\n{'=' * 60}")
    print(f"Saving to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(locations, f, indent=2)
    
    print(f"\n✓ Complete!")
    print(f"  - Successfully enriched: {success_count}/{len(locations)}")
    print(f"  - Failed/No image: {fail_count}/{len(locations)}")
    print(f"  - Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
