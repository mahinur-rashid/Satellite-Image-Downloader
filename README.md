# Satellite Image Downloader

A Flask web application for downloading nighttime satellite imagery from Google Earth Engine.

## Overview

This tool allows users to download VIIRS nighttime satellite imagery for multiple countries. It includes features like:
- Multi-country selection
- Automatic resolution validation
- Progress tracking
- Google Earth Engine integration
- Easy-to-use web interface

## Prerequisites

1. [Sign up for Google Earth Engine](https://signup.earthengine.google.com/)
2. [Create a Google Cloud Project](https://console.cloud.google.com/projectcreate)
3. Enable Earth Engine API in your project
4. Python 3.8 or higher

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mahinur-rashid/satellite-image-downloader.git
cd satellite-image-downloader
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory and add your Earth Engine project ID:
```bash
project='your-earth-engine-project-id'
```

5. Authenticate with Earth Engine:
```bash
earthengine authenticate
```

6. Start the application:
```bash
python app.py
```

The application will be available at: http://localhost:5000

## Environment Setup

The application uses environment variables for configuration:
- `project`: Your Google Earth Engine project ID
  - Find this in your Google Cloud Console
  - Format: 'ee-yourprojectname'

## Usage

1. Select one or more countries from the list
2. Choose the year range (2013-2024)
3. Set the resolution (500m-5000m)
4. Click "Download Images"

Images will be saved in the `downloads` folder.

## Technical Details

- Uses NOAA/VIIRS/001/VNP46A1 dataset
- Maximum file size: 64MB per image
- Images are saved in GeoTIFF format
- Coordinate system: EPSG:4326

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This repository is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

Copyright (c) Mahinur Rashid, Kazi Iftekharul Adnan


