# Geospatial File Measurement API

A Django REST Framework API for uploading and processing geospatial files (`.zip` Shapefiles and `.kml`), extracting feature information, handling coordinate reference systems (CRS), and calculating geometry measurements.

## Features

- Upload `.zip` Shapefile datasets and `.kml` files
- Extract geospatial features using GeoPandas
- Store file-level and feature-level information in PostgreSQL/SQLite
- Detect and store the source CRS
- Transform geographic CRS to an appropriate projected CRS before measurement
- Calculate:
  - **Polygon / MultiPolygon** → Area
  - **LineString** → Length
  - **Point** → No measurement
- REST APIs for file information and feature measurements

---

# 1. Setup
## Requirements

Make sure the following are installed:

- Python 3.10+


## Clone the repository

```bash
git clone https://github.com/sdameer/GeoSpat.git
cd Geo
```

## Create a virtual environment

### Windows

```bash
pip install virtualenv
python -m venv venv
venv\Scripts\activate
```


## Install dependencies

```bash
pip install -r requirements.txt
```


## Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

# 2. API Documentation

## Upload Geospatial File

### Endpoint

```http
POST /api/files/
```

### Description

Uploads and processes a geospatial file.

Supported formats:

- `.zip` containing a Shapefile
- `.kml`

### Request

Use `multipart/form-data`.

| Key | Type | Value |
|---|---|---|
| `file` | File | Geospatial file |


### Example Response

```json
{
    "id": 1,
    "filename": "ne_110m_admin_0_countries.zip",
    "feature_count": 177,
    "crs": "EPSG:4326",
    "status": "COMPLETED"
}
```

---

#  Get File Information

### Endpoint

```http
GET /api/files/{id}/
```

### Example

```http
GET /api/files/1/
```

### Example Response

```json
{
    "id": 1,
    "file_name": "ne_110m_admin_0_countries.zip",
    "crs": "EPSG:4326",
    "feature_count": 177,
    "status": "COMPLETED"
}
```

---

#  Get Feature Measurements

### Endpoint

```http
GET /api/files/{id}/measurements/
```

### Description

Returns measurements calculated for each feature in the uploaded file.

### Example

```http
GET /api/files/1/measurements/
```

### Example Response

```json
{
    "id": 1,
    "file_name": "ne_110m_admin_0_countries.zip",
    "crs": "EPSG:4326",
    "feature_count": 177,
    "status": "COMPLETED",
    "measurements": [
        {
            "feature_index": 0,
            "geometry_type": "MultiPolygon",
            "area": 19291102006.342243,
            "length": null
        },
        {
            "feature_index": 1,
            "geometry_type": "Polygon",
            "area": 934643655650.0198,
            "length": null
        }
    ]
}
```

### Measurement rules

| Geometry | Measurement |
|---|---|
| Polygon | Area in square meters |
| MultiPolygon | Area in square meters |
| LineString | Length in meters |
| Point | No measurement |

---

# 3. Architecture

The application is divided into three main responsibilities:

```text
Client / Postman
       |
       v
Django REST API
       |
       v
Serializer / Processing Logic
       |
       +------> GeoPandas
       |
       +------> CRS Transformation
       |
       +------> Measurement Calculation
       |
       v
Database
       |
       +------> GeoSpatialFile
       |
       +------> GeoFeature
```

## Application Structure

A simplified project structure:

```text
project/
│
├── manage.py
├── requirements.txt
├── README.md
├── .env
│
├── project/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
└── app_geo/
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    └── ...
```

### Main models

#### `GeoSpatialFile`

Stores information about the uploaded file:

- File
- File name
- CRS
- Feature count
- Processing status

#### `GeoFeature`

Stores information about each individual feature:

- Feature index
- Geometry type
- Geometry
- Properties
- Area
- Length

One uploaded file can therefore have many features:

```text
GeoSpatialFile
      |
      +---- GeoFeature
      +---- GeoFeature
      +---- GeoFeature
      +---- ...
```

---

# 4. File Processing Flow

When a file is uploaded:

```text
Upload file
     ↓
Validate file extension
     ↓
Save uploaded file
     ↓
Read file using GeoPandas
     ↓
Check whether features exist
     ↓
Read CRS
     ↓
Process every feature
     ↓
Calculate measurements
     ↓
Store GeoFeature records
     ↓
Update file status
     ↓
Return API response
```

GeoPandas reads the geospatial dataset and provides:

- Geometry
- Geometry type
- CRS
- Feature properties

The feature information is then stored in the database.

---

# 5. Measurement Calculation Flow

Measurements depend on the geometry type.

```text
Feature
   |
   +---- Polygon / MultiPolygon
   |          ↓
   |        Calculate Area
   |
   +---- LineString
   |          ↓
   |        Calculate Length
   |
   +---- Point
              ↓
         No measurement
```

The application uses Shapely/GeoPandas geometry operations:

```python
geometry.area
geometry.length
```

However, these calculations are performed **after CRS transformation** when the original CRS is geographic.

---

# 6. CRS Handling

Coordinate Reference Systems are important because geographic coordinates such as latitude and longitude are measured in degrees rather than meters.

For example:

```text
EPSG:4326
```

represents geographic coordinates:

```text
longitude, latitude
```

Calculating area or distance directly from these coordinates would not produce measurements in meaningful real-world units.

Therefore, the application checks whether the source CRS is geographic.

```text
Input CRS
   |
   v
Is it geographic?
   |
   +---- No ----> Calculate measurement
   |
   +---- Yes
          |
          v
   Estimate suitable UTM CRS
          |
          v
   Transform geometry
          |
          v
   Calculate measurement
```

The application uses:

```python
projected_crs = feature_gdf.estimate_utm_crs()
feature_gdf = feature_gdf.to_crs(projected_crs)
```

After transformation, the projected coordinates are generally represented in meters.

Therefore:

```text
Polygon / MultiPolygon
        ↓
area
        ↓
square meters (m²)

LineString
        ↓
length
        ↓
meters (m)
```

For the sample Natural Earth dataset, the original CRS is:

```text
EPSG:4326
```

The application transforms the geometry to an appropriate projected CRS before calculating measurements.

---

#  Testing the API

The APIs can be tested using:

- Postman
- cURL
- Any REST API client

### Recommended testing sequence

First upload a file:

```http
POST /api/files/
```

Then use the returned ID:

```http
GET /api/files/1/
```

Finally:

```http
GET /api/files/1/measurements/
```

---

#  Example Dataset

The project was tested using the Natural Earth Admin 0 Countries dataset.

The sample dataset contains:

- 177 features
- 148 Polygon features
- 29 MultiPolygon features
- CRS: EPSG:4326

The dataset was successfully processed and measurements were calculated after CRS transformation.

---

#  Tech Stack

- **Python**
- **Django**
- **Django REST Framework**
- **GeoPandas**
- **Shapely**
- **SQLite**
- **Postman** for API testing

---


