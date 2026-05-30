import os
import sys
import math
import time
import requests

# BBOX for Ba Đình Ward
BBOX = (21.028, 105.822, 21.050, 105.850)
ZOOM_LEVELS = [13, 14, 15, 16, 17]

# User agent for OSM policy compliance
HEADERS = {
    'User-Agent': 'MapTrackingOfflineAgent/1.0 (manhnguyen@project.ai_intro)'
}

def deg2num(lat_deg, lon_deg, zoom):
    """Convert latitude/longitude to OpenStreetMap tile coordinates (x, y)."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def download_tiles(bbox=BBOX, zooms=ZOOM_LEVELS, output_dir=None):
    """
    Download OSM map tiles within a bounding box for specified zoom levels.
    Saves tiles to {output_dir}/{z}/{x}/{y}.png
    """
    if output_dir is None:
        # Default to static/tiles directory relative to this script
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'tiles')

    min_lat, min_lon, max_lat, max_lon = bbox
    total_tiles = 0
    downloaded_tiles = 0
    skipped_tiles = 0

    print(f"[tile_download] Starting tile download for BBOX: {bbox}")
    print(f"[tile_download] Target Zoom Levels: {zooms}")
    print(f"[tile_download] Output Directory: {output_dir}")

    # Step 1: Calculate total tiles to download
    for zoom in zooms:
        x_start, y_start = deg2num(max_lat, min_lon, zoom)
        x_end, y_end = deg2num(min_lat, max_lon, zoom)
        
        # Adjust order because y increases from North to South (max_lat corresponds to min_y)
        x_range = range(min(x_start, x_end), max(x_start, x_end) + 1)
        y_range = range(min(y_start, y_end), max(y_start, y_end) + 1)
        total_tiles += len(x_range) * len(y_range)

    print(f"[tile_download] Total tiles to fetch/verify: {total_tiles}")

    # Step 2: Download the tiles
    for zoom in zooms:
        x_start, y_start = deg2num(max_lat, min_lon, zoom)
        x_end, y_end = deg2num(min_lat, max_lon, zoom)
        
        x_range = range(min(x_start, x_end), max(x_start, x_end) + 1)
        y_range = range(min(y_start, y_end), max(y_start, y_end) + 1)

        print(f"[tile_download] Zoom {zoom}: X range ({min(x_range)} to {max(x_range)}), Y range ({min(y_range)} to {max(y_range)})")

        for x in x_range:
            for y in y_range:
                tile_url = f"https://a.basemaps.cartocdn.com/rastertiles/voyager/{zoom}/{x}/{y}.png"
                tile_dir = os.path.join(output_dir, str(zoom), str(x))
                tile_path = os.path.join(tile_dir, f"{y}.png")

                # Skip if already exists
                if os.path.exists(tile_path):
                    skipped_tiles += 1
                    continue

                os.makedirs(tile_dir, exist_ok=True)

                try:
                    resp = requests.get(tile_url, headers=HEADERS, timeout=10)
                    if resp.status_code == 200:
                        with open(tile_path, 'wb') as f:
                            f.write(resp.content)
                        downloaded_tiles += 1
                        # Polite delay to respect OSM servers usage policy
                        time.sleep(0.1)
                    else:
                        print(f"[tile_download] Error: Received status {resp.status_code} for tile {zoom}/{x}/{y}")
                except Exception as e:
                    print(f"[tile_download] Exception failed to download tile {zoom}/{x}/{y}: {e}")

                # Print progress every 10 tiles
                processed = downloaded_tiles + skipped_tiles
                if processed % 20 == 0 or processed == total_tiles:
                    percent = (processed / total_tiles) * 100
                    print(f"[tile_download] Progress: {percent:.1f}% ({processed}/{total_tiles} verified, {downloaded_tiles} downloaded)")

    print(f"[tile_download] Completed. Downloaded: {downloaded_tiles}, Skipped: {skipped_tiles}, Total Verified: {downloaded_tiles + skipped_tiles}")

if __name__ == '__main__':
    # If run directly, save to MapTracking/static/tiles
    download_tiles()
