import ee
import pandas as pd
import os
import requests
import urllib3
import ast
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PROJECT_ID = os.getenv('project')

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def process_country_month(country, year, month, resolution):
    """Process one month of data for a country"""
    try:
        monthStr = f"0{month}" if month < 10 else str(month)
        
        # Fix the date creation
        start = ee.Date(f"{year}-{monthStr}-01")
        end = start.advance(1, 'month')
        
        countryBoundaries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
        country_feature = countryBoundaries.filter(ee.Filter.eq('country_na', country))
        country_geometry = country_feature.geometry()
        
        mask = ee.Image(0).paint(country_feature, 1).selfMask()
        
        viirs = ee.ImageCollection('NOAA/VIIRS/001/VNP46A1') \
            .filter(ee.Filter.date(start, end)) \
            .select('DNB_At_Sensor_Radiance_500m')
        
        composite = viirs.mean() \
            .multiply(mask) \
            .clip(country_geometry)
        
        bounds = country_geometry.bounds(1000)
        
        url = composite.getDownloadURL({
            'scale': resolution,
            'region': bounds,
            'format': 'GeoTIFF',
            'fileNamePrefix': f"{country}_{year}_{monthStr}",
            'crs': 'EPSG:4326',
            'maxPixels': 1e13,
            'clipToRegion': True
        })
        
        return [{
            'url': url,
            'country': country,
            'year': year,
            'month': monthStr
        }]
    except Exception as e:
        print(f"Error processing {country} for {year}-{month}: {str(e)}")
        return []

def validate_resolution(country, resolution):
    """Validate if the requested resolution is possible for the country size"""
    try:
        # Simple initialization check
        if not ee.data._initialized:
            ee.Initialize(project=PROJECT_ID)
        
        countryBoundaries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
        country_feature = countryBoundaries.filter(ee.Filter.eq('country_na', country))
        country_geometry = country_feature.geometry()
        
        # Calculate approximate image size
        bounds = country_geometry.bounds().getInfo()
        width = abs(bounds['coordinates'][0][2][0] - bounds['coordinates'][0][0][0])
        height = abs(bounds['coordinates'][0][2][1] - bounds['coordinates'][0][0][1])
        
        pixels = (width * 111320 / resolution) * (height * 111320 / resolution)
        estimated_size = (pixels * 4) / (1024 * 1024)  # Rough estimate in MB
        
        if estimated_size > 60:  # Leave some margin for the 64MB limit
            suggested_resolution = int(resolution * (estimated_size / 60) ** 0.5)
            return False, suggested_resolution
        return True, resolution
    except Exception as e:
        print(f"Error in validate_resolution: {str(e)}")
        return True, resolution  # Default to allowing the resolution if validation fails

def download_images(countries, start_year, end_year, resolution, save_folder):
    """Download images for selected countries and date range"""
    results = []
    
    for country in countries:
        # Validate resolution for each country
        is_valid, suggested_res = validate_resolution(country, resolution)
        if not is_valid:
            results.append({
                'country': country,
                'status': 'error',
                'message': f'Resolution too high. Please use {suggested_res}m or higher.'
            })
            continue
            
        try:
            urls = []
            for year in range(start_year, end_year + 1):
                for month in range(1, 13):
                    try:
                        urls.extend(process_country_month(country, year, month, resolution))
                    except ee.EEException as e:
                        results.append({
                            'country': country,
                            'status': 'error',
                            'message': f'Error processing {year}-{month}: {str(e)}'
                        })
                        continue
            
            if urls:
                csv_path = save_urls_to_csv(urls, country, save_folder)
                download_from_csv(csv_path)
                results.append({
                    'country': country,
                    'status': 'success',
                    'message': f'Downloaded {len(urls)} images'
                })
                
        except Exception as e:
            results.append({
                'country': country,
                'status': 'error',
                'message': str(e)
            })
    
    return results

def save_urls_to_csv(urls, country, save_folder):
    """Save download URLs to a CSV file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(save_folder, f'{country}_{timestamp}_urls.csv')
    
    # Create DataFrame directly from list of dictionaries
    df = pd.DataFrame(urls)
    df['downloaded'] = False
    
    # Convert dictionary columns to strings if needed
    for col in df.columns:
        if isinstance(df[col].iloc[0], dict):
            df[col] = df[col].apply(str)
    
    df.to_csv(csv_path, index=False)
    return csv_path

def download_from_csv(csv_path):
    """Download files from URLs stored in CSV"""
    df = pd.read_csv(csv_path)
    save_folder = os.path.dirname(csv_path)
    
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    
    for index, row in df.iterrows():
        if not row['downloaded']:
            try:
                # Direct access to columns instead of parsing
                url = row['url']
                country = row['country']
                year = row['year']
                month = row['month']
                
                # Create filename with correct format
                filename = f"{country}_{year}_{month}.tif"
                file_path = os.path.join(save_folder, filename)
                
                print(f"Downloading: {filename}")
                response = session.get(url, verify=False)
                
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    df.at[index, 'downloaded'] = True
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download {filename}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"Error downloading image {index}: {str(e)}")
                continue
    
    df.to_csv(csv_path, index=False)
