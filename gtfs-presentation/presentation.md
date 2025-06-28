---
title: "GTFS"
author: "Jack Rosenthal"
date: \today
theme: "default"
colortheme: "default"
fonttheme: "default"
aspectratio: 169
fontsize: 9pt
---

# Introduction

## What is GTFS?

- **General Transit Feed Specification**
- Standardized format for public transportation schedules and geographic information
- Open data format used worldwide
- Developed by Google in collaboration with TriMet (Portland)

## GTFS vs GTFS-RT

- **GTFS (Static)**: Scheduled transit data
  - Routes, stops, schedules, fares
  - Published as ZIP files containing CSV files
- **GTFS-RT (Realtime)**: Live transit updates
  - Trip updates, vehicle positions, service alerts
  - Published as Protocol Buffer feeds

## How GTFS-RT Depends on GTFS

- GTFS-RT references GTFS entities by ID
- **trip_id**, **route_id**, **stop_id** from GTFS static data
- GTFS-RT provides real-time updates to the static schedule
- Cannot interpret GTFS-RT without the corresponding GTFS feed

# GTFS Static Data Structure

## ZIP File Contents

GTFS is distributed as a ZIP file containing CSV files:

- **Required files**: agency.txt, stops.txt, routes.txt, trips.txt, stop_times.txt
- **Optional files**: calendar.txt, calendar_dates.txt, feed_info.txt, shapes.txt, fare_*.txt

## feed_info.txt Example (RTD Denver)

```csv
feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version
RTD,http://rtd-denver.com,en,20250525,20250830,May25-35159-6-8-20250526-030137
```

- Provides metadata about the GTFS feed
- Publisher information and validity period

## agency.txt Example (RTD Denver)

```csv
agency_id,agency_name,agency_url,agency_timezone,agency_lang
RTD,Regional Transportation District,http://rtd-denver.com,America/Denver,en
```

- Defines transit agencies in the feed
- Required for all GTFS feeds

## calendar.txt Example (RTD Denver)

```csv
service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
DPSWK,1,1,1,1,1,0,0,20250525,20250830
FR,0,0,0,0,1,0,0,20250525,20250830
```

- Defines service patterns (which days service runs)
- 1 = service runs, 0 = no service

## calendar_dates.txt Example (RTD Denver)

```csv
service_id,date,exception_type
DPSWK,20250526,2
DPSWK,20250704,2
FR,20250704,2
```

- **exception_type**: 1 = service added, 2 = service removed
- Handles holidays and special service changes

## routes.txt Example (RTD Denver)

```csv
route_id,agency_id,route_short_name,route_long_name,route_type,route_color
DASH,RTD,DASH,Boulder / Lafayette via Louisville,3,0076CE
JUMP,RTD,JUMP,Boulder / Lafayette/ Erie,3,0076CE
BOND,RTD,BOUND,30th Street,3,0076CE
```

- **route_type**: 3 = Bus, 1 = Light Rail, 0 = Tram
- Colors for map display

## stops.txt Example (RTD Denver)

```csv
stop_id,stop_code,stop_name,stop_lat,stop_lon,wheelchair_boarding
24591,24591,Downtown Boulder Station Gate F,40.01698,-105.27697,1
12490,12490,Broadway & Canyon Blvd,40.015157,-105.279133,1
33236,33236,Downtown Boulder Station Gate A,40.017263,-105.276845,1
```

- Geographic coordinates for all stops
- **wheelchair_boarding**: 1 = accessible, 0 = not accessible

## trips.txt Example (RTD Denver)

```csv
trip_id,route_id,service_id,trip_headsign,direction_id,block_id
115374480,DASH,SA,Lafayette PnR Willoughby,0,DASH  1
115374508,DASH,SA,Dtwn Boulder,1,DASH  1
115374639,JUMP,SA,Erie Community Center,0,JUMP  9
115368530,BOND,SA,28th/Iris,0,BOND  1
```

- Links routes to specific scheduled trips
- **direction_id**: Unique identifier for direction (0 or 1)
- **trip_headsign**: Destination shown to passengers
- **block_id**: Groups trips operated by the same vehicle

## Block ID

![](block_id.jpg)

## stop_times.txt Example (RTD Denver)

```csv
trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type
115350006,11:29:00,11:29:00,26175,1,0,1
115350006,11:30:56,11:30:56,20171,2,0,0
115350006,11:32:18,11:32:18,20094,3,0,0
```

- Defines when vehicles arrive/depart at each stop
- **pickup_type/drop_off_type**: 0 = regular, 1 = no pickup/drop-off

# GTFS-RT (Realtime)

## Three Feed Types

- **Trip Updates**: Real-time updates for estimated arrival times at each stop
- **Vehicle Positions**: Real-time vehicle locations
- **Service Alerts**: Disruptions, detours, other notices

## RTD Denver GTFS-RT URLs

- **Trip Updates**: `https://www.rtd-denver.com/files/gtfs-rt/TripUpdate.pb`
- **Vehicle Positions**: `https://www.rtd-denver.com/files/gtfs-rt/VehiclePosition.pb`
- **Service Alerts**: `https://www.rtd-denver.com/files/gtfs-rt/Alerts.pb`
- **Static GTFS**: `https://www.rtd-denver.com/files/gtfs/google_transit.zip`

## Trip Update Example (RTD)

```protobuf
trip_update {
  trip {
    trip_id: "115350015"
    schedule_relationship: SCHEDULED
    route_id: "0"
    direction_id: 0
  }
  stop_time_update {
    stop_sequence: 35
    arrival {
      time: 1751140998
    }
    departure {
      time: 1751140998
    }
    stop_id: "17834"
    schedule_relationship: SCHEDULED
  }
  vehicle {
    label: "9348"
  }
}
```

- Real-time arrival/departure predictions
- References GTFS trip and stops by ID

## Service Alert Example (RTD)

```protobuf
active_period {
  start: 1699869600
  end: 1785488340
}
informed_entity {
  agency_id: "RTD"
  route_id: "0L"
  route_type: 3
  stop_id: "12463"
}
cause: CONSTRUCTION
effect: NO_SERVICE
header_text {
  translation {
    text: "The following stop is closed through Thu Jul 30 due to construction: Broadway & W 9th Ave (#12463)."
    language: "en"
  }
}
```

- Alerts about service disruptions with human-readable text
- References GTFS static data (route_id, stop_id)

## Vehicle Position Example (RTD)

```protobuf
trip {
  trip_id: "115374558"
  schedule_relationship: SCHEDULED
  route_id: "DASH"
  direction_id: 1
}
position {
  latitude: 39.986282
  longitude: -105.20412
  bearing: 268.0
}
current_status: IN_TRANSIT_TO
vehicle {
  label: "6220"
}
```

- Real-time vehicle locations
- Links to GTFS trip via **trip_id**

# Questions?

Thank you for your attention!