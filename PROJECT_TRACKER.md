# Network Device Geolocation Mapper - Project Tracker

## Project Overview
A web-based application for mapping network devices to physical office locations. Designed for IT/security teams to visualize where devices are located based on subnet-to-office mappings.

**Target Users:** 5-20 engineers  
**Hosting:** IIS on internal server (Port 8080)  
**Server Hostname:** edcv-utl-idd1  
**Data Storage:** PostgreSQL 18  
**Authentication:** None (internal network only)

## Current Status: ✅ OPERATIONAL

**Application URL:** http://edcv-utl-idd1:8080

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Server: edcv-utl-idd1                          │
│                                                             │
│   IIS (Port 8080)                Flask API (Port 5050)      │
│   └── NetworkMapper Site         ├── /api/offices           │
│       └── index.html ◄──────────►├── /api/clients           │
│              │                   ├── /api/atera/*           │
│              │                   └── /api/devices           │
│              │                            │                 │
│         Direct API Call                   ▼                 │
│    (http://edcv-utl-idd1:5050)   PostgreSQL 18              │
│                                  └── network_mapper_db      │
└─────────────────────────────────────────────────────────────┘
                    ▲
              Users browse to
         http://edcv-utl-idd1:8080
```

---

## Environment Status (2026-01-19)

| Component | Status | Details |
|-----------|--------|---------|
| Python | ✅ Verified | 3.14.2 |
| pip / Flask | ✅ Installed | flask, flask-cors, psycopg2-binary |
| PostgreSQL | ✅ Running | Version 18, network_mapper_db created |
| IIS | ✅ Running | Port 8080, NetworkMapper site |
| Flask API | ✅ Running | Port 5050 |
| Atera API | ✅ Configured | API key in config.py |
| Nominatim API | ✅ Integrated | City coordinate lookup |

---

## Feature Status

### ✅ Completed Features

| Feature | Description | Version |
|---------|-------------|---------|
| Excel Import | Parse .xlsx files, extract device IPs | v1 |
| Subnet Detection | Auto-detect unique subnets from imported data | v1 |
| Office Library | Add/edit/remove office locations (PostgreSQL) | v8 |
| City Search | Local database + Nominatim API + manual entry | v9 |
| Subnet Mapping | Assign subnets to offices with Office/Remote type | v2 |
| Interactive Map | Leaflet.js with CartoDB dark tiles | v1 |
| Location Clustering | One marker per office showing device count | v2 |
| Device View | Individual device markers (scattered) | v2 |
| Filtering | Filter by All/Office/Remote/Unmapped | v1 |
| Sidebar | Expandable location groups with device lists | v2 |
| New Client Wizard | 3-step guided import process | v3 |
| Map Refresh | Fix tile loading issues without data loss | v6 |
| Export CSV | Summary report export | v1 |
| Local Backup | JSON export/import for offline backup | v6 |
| PostgreSQL Integration | Full database persistence | v8 |
| Flask API | REST API for all database operations | v8 |
| IIS Hosting | Standalone site on port 8080 | v8 |
| Load/Save Client | Persist and retrieve client mappings | v8 |
| Delete Client | Remove client data from database | v8 |
| Atera API Integration | Hybrid import - Excel or direct from Atera | v9 |
| Auto IP Geolocation | Public IPs auto-located via ip-api.com | v9 |
| Nominatim City Search | OpenStreetMap-based coordinate lookup | v9 |
| Auto Office Creation | Create office from Atera customer address | v9 |
| Offices Without Coords | Support offices that appear only in sidebar | v9 |
| MA-1 Import | Bulk import office locations from MA-1 Excel | v10 |
| Office Library Redesign | State-grouped collapsible sections | v10 |
| City/State Schema | Separate city and state fields in database | v10 |
| **MA-1 Edit/Retry** | Edit "not found" locations and retry geocoding | v11 |
| **MA-1 Deduplication** | Merge duplicate city/state entries before import | v11 |
| **Step 1 Workflow Redesign** | Two-path layout: Recommended (MA-1) vs Continue | v11 |
| **Grouped Office Dropdown** | Offices grouped by state, recently added at top | v11 |
| **Map Auto-Refresh** | Multiple strategies to fix tiles on first load | v11 |
| **Improved Text Contrast** | Brighter text colors throughout for readability | v11 |
| **API Data Truncation** | Handle long MAC addresses and other fields | v11 |
| **Duplicate IP Handling** | Skip duplicate IPs when saving devices | v11 |

### 🔄 In Progress

| Feature | Description | Status |
|---------|-------------|--------|
| IIS Reverse Proxy | Route /api to Flask (currently using direct URL) | Optional improvement |
| Task Scheduler | Auto-start Flask API on server reboot | To configure |

### ❌ Abandoned

| Feature | Description | Reason |
|---------|-------------|--------|
| SharePoint Integration | Store data in SharePoint Lists | JavaScript blocked in SP document viewer |
| MA-1 "Remote" Detection | Skip sites with "remote" in name | "Remote" in MA-1 means remote office, not remote worker |

### 📋 Planned / Future

| Feature | Description | Priority |
|---------|-------------|----------|
| **Delete Companies** | Remove companies from the system | High |
| Authentication | Track who created/modified data | Low |
| Audit Trail | Log changes with timestamps and users | Low |
| Map Themes | Light/dark/satellite tile options | Low |
| Device Search | Search devices by name/IP across clients | Medium |
| Subnet Auto-Suggest | Suggest office based on similar client subnets | Low |
| Searchable Dropdown | Type-to-filter office selection | Medium |

---

## PostgreSQL Database Schema

**Database:** `network_mapper_db`

### 1. office_locations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Office name (e.g., "Chicago, IL") |
| city | VARCHAR(100) | | City name (e.g., "Chicago") |
| state | VARCHAR(10) | | State code (e.g., "IL") |
| latitude | DECIMAL(9,6) | | Decimal degrees (NULL = sidebar only) |
| longitude | DECIMAL(9,6) | | Decimal degrees (NULL = sidebar only) |
| created_at | TIMESTAMP | DEFAULT NOW() | When record was created |

### 2. clients
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Client name |
| created_at | TIMESTAMP | DEFAULT NOW() | When client was first saved |
| updated_at | TIMESTAMP | DEFAULT NOW() | When client was last updated |

### 3. client_mappings
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| client_id | INTEGER | FOREIGN KEY → clients(id) | References client |
| subnet | VARCHAR(15) | NOT NULL | Subnet (e.g., "192.168.1") |
| office_name | VARCHAR(255) | NOT NULL | References office name |
| mapping_type | VARCHAR(10) | NOT NULL | "office" or "remote" |

### 4. client_devices
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| client_id | INTEGER | FOREIGN KEY → clients(id) | References client |
| name | VARCHAR(255) | NOT NULL | Device name |
| ip_address | VARCHAR(50) | NOT NULL | Device IP |
| mac_address | VARCHAR(500) | | MAC address(es) - expanded for Atera |
| device_type | VARCHAR(100) | | Type from Excel/Atera |
| manufacturer | VARCHAR(200) | | Device manufacturer |
| os | VARCHAR(200) | | Operating system |

**Note:** `mac_address` column was expanded from VARCHAR(17) to VARCHAR(500) on 2026-01-19 to accommodate Atera's multiple MAC address format.

---

## Recent Changes (2026-01-19)

### Step 1 Wizard Redesign
- **Two-path workflow** at top of Step 1:
  - **Recommended** (green): "First time with this client?" → Import MA-1 First
  - **Alternative** (gray): "Offices already in library?" → Continue to Device Import
- Clear visual separation between workflow choice and device import section
- Client name included in subnet mapping instructions

### MA-1 Import Improvements
- **Edit/Retry for "Not Found"**: Edit button on each not-found entry, inline text editing, retry search with edited text
- **Deduplication**: Merge duplicate city/state combinations before display (e.g., two Columbia, SC sites become one entry showing "From 2 sites: ...")
- **Reads City/State rows directly**: Changed from parsing Site Name (Row 22) to reading City (Row 25) and State (Row 26) directly
- **Removed "remote" keyword detection**: "Remote" in MA-1 context means remote office location, not remote worker
- **Dynamic button**: Shows "Done" instead of "Add Selected Offices" when all locations already in library

### Grouped Office Dropdown
- Offices organized by state with optgroup headers (── SC ──, ── CT ──, etc.)
- "Recently Added" section at top shows offices imported via MA-1 in current session
- Better color contrast: dark blue background (#1e293b) with light text (#e2e8f0)
- State headers in blue (#60a5fa) for visual distinction

### Map Auto-Refresh
- Multiple `invalidateSize()` calls at 100ms, 300ms, 500ms, 1s, 2s after page load
- Tile layer `loading` and `load` event handlers
- ResizeObserver watching map container
- Visibility change handler for tab switching
- **Map now loads correctly on first visit without manual refresh**

### Text Contrast Improvements
- Brightened muted text from #64748b/#94a3b8 to #b8c5d6
- Modal text and form labels now use #cbd5e1
- Headings (h3) use #e2e8f0

### API Fixes (api_server.py)
- **Data truncation**: All fields truncated to prevent database overflow
  - name: 255 chars, ip_address: 50 chars, mac_address: 500 chars
  - device_type: 100 chars, manufacturer/os: 200 chars
- **Duplicate IP handling**: Skip duplicate IPs within same batch (tracks seen IPs)
- **Better error logging**: Full traceback printed to console on errors
- **Commit before insert**: DELETE committed before INSERT to avoid constraint issues

### Database Schema Change
```sql
ALTER TABLE client_devices ALTER COLUMN mac_address TYPE VARCHAR(500);
```
Required for Atera imports where devices have multiple MAC addresses.

---

## File Inventory

| File | Purpose | Location |
|------|---------|----------|
| index.html | Main application | C:\inetpub\wwwroot\NetworkMapper\ |
| api_server.py | Flask REST API | E:\Apps\NetworkMapper\ |
| config.py | Database & Atera credentials | E:\Apps\NetworkMapper\ |
| migrate_offices.sql | Schema migration script | E:\Apps\NetworkMapper\ |
| PROJECT_TRACKER.md | This document | Project folder |

### Development Workflow
```
C:\DEV\NetworkMapper\           <- Development
├── frontend\
│   └── index.html
├── backend\
│   └── api_server.py
└── deploy.bat                  <- Copies to production

C:\inetpub\wwwroot\NetworkMapper\  <- IIS Production
└── index.html

E:\Apps\NetworkMapper\          <- API Production
├── api_server.py
└── config.py
```

---

## Setup Checklist

### Server Setup (edcv-utl-idd1) ✅ COMPLETE
- [x] Python installed (3.14.2)
- [x] pip works
- [x] Flask installed
- [x] psycopg2-binary installed
- [x] PostgreSQL 18 running
- [x] Database `network_mapper_db` created
- [x] Tables created
- [x] API deployed and running on port 5050
- [x] Atera API key configured

### IIS Setup ✅ COMPLETE
- [x] IIS running
- [x] NetworkMapper site created (port 8080)
- [x] index.html deployed
- [x] Application accessible

### Database Migration (2026-01-17) ✅ COMPLETE
- [x] Run `migrate_offices.sql` to add city/state columns
- [x] Verify existing offices parsed correctly
- [x] Deploy updated api_server.py
- [x] Deploy updated index.html

### Database Update (2026-01-19) ✅ COMPLETE
- [x] Expand mac_address column to VARCHAR(500)

### Team Rollout
- [ ] Share URL with team (http://edcv-utl-idd1:8080)
- [ ] Provide quick-start guide
- [ ] Configure Task Scheduler for API auto-start

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-01-14 | Initial app with local storage |
| v2 | 2026-01-14 | Location clustering, view modes |
| v3 | 2026-01-14 | Client workflow, import wizard |
| v4 | 2026-01-14 | City search (API - failed) |
| v5 | 2026-01-14 | City search (local database) |
| v6 | 2026-01-14 | Hybrid city search, manual entry, map refresh |
| v7 | 2026-01-15 | SharePoint integration (failed - JS blocked) |
| v8 | 2026-01-16 | PostgreSQL + IIS integration (working) |
| v9 | 2026-01-16 | Atera API, Nominatim, auto-office creation |
| v10 | 2026-01-17 | MA-1 import, Office Library redesign, city/state schema |
| v11 | 2026-01-19 | MA-1 edit/retry, deduplication, Step 1 redesign, grouped dropdowns, map auto-refresh, API fixes |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/offices | List all offices |
| POST | /api/offices | Create office (name, city, state, lat, lng) |
| DELETE | /api/offices/:id | Delete office |
| GET | /api/clients | List all clients |
| POST | /api/clients | Create client |
| DELETE | /api/clients/:id | Delete client |
| GET | /api/clients/:id/full | Get client with mappings & devices |
| POST | /api/clients/:id/mappings | Save subnet mappings |
| POST | /api/clients/:id/devices | Save devices |
| GET | /api/atera/customers | List Atera customers |
| GET | /api/atera/customers/:id/devices | Get devices for customer |

---

## Known Issues / Limitations

1. ~~**Map tile loading** - Occasionally fails; use Refresh Map button~~ **FIXED v11**
2. **Large datasets** - Performance may degrade with 1000+ devices
3. **Concurrent editing** - Last-write-wins (no real-time sync)
4. **API auto-start** - Flask must be manually started after server reboot
5. **Direct API URL** - Uses http://edcv-utl-idd1:5050 (reverse proxy not configured)

---

## Lessons Learned

### SharePoint Document Hosting (2026-01-15)
SharePoint document libraries do **not** execute JavaScript properly. HTML files are either shown in preview mode that blocks JS or downloaded.

**Resolution:** Switched to IIS + PostgreSQL architecture.

### Port Conflicts (2026-01-16)
Port 5001 was already in use by "Live Tenant Analyzer" application.

**Resolution:** Changed Flask API to port 5050.

### State Grouping (2026-01-17)
Parsing state from freeform office names is unreliable. "Chicago Office" can't determine state.

**Resolution:** Added dedicated `city` and `state` columns to database schema.

### Nominatim for Accurate Data (2026-01-17)
Parsed MA-1 site names often have inaccurate city/state (e.g., "Atlanta Area (Marietta)" → "Marietta, Atlanta"). Nominatim API returns accurate geocoded data.

**Resolution:** Use Nominatim-provided city/state for display and storage, not parsed values.

### MA-1 "Remote" Keyword (2026-01-19)
Initially skipped MA-1 sites containing "remote" thinking they were remote workers. In MA-1 context, "remote" means a remote office location, not work-from-home.

**Resolution:** Removed all "remote" keyword detection from MA-1 import.

### MA-1 Data Structure (2026-01-19)
Initially parsed city/state from Site Name (Row 22) which was unreliable. MA-1 has dedicated rows for City (Row 25) and State (Row 26).

**Resolution:** Read directly from structured City/State rows instead of parsing Site Name.

### Atera MAC Addresses (2026-01-19)
Atera returns multiple MAC addresses as comma-separated strings that exceeded VARCHAR(17) limit.

**Resolution:** Expanded mac_address column to VARCHAR(500) and added field truncation in API.

### Duplicate Device IPs (2026-01-19)
Atera can return devices with duplicate IPs (multiple network adapters), causing unique constraint violations.

**Resolution:** Track seen IPs and skip duplicates within same save batch.

---

## Contacts / Resources

- **Application URL:** http://edcv-utl-idd1:8080
- **API URL:** http://edcv-utl-idd1:5050/api
- **PostgreSQL:** localhost:5432 on edcv-utl-idd1
- **Leaflet Docs:** leafletjs.com/reference.html
- **SheetJS Docs:** docs.sheetjs.com
- **Flask Docs:** flask.palletsprojects.com
- **Nominatim API:** nominatim.openstreetmap.org
- **Atera API Docs:** app.atera.com/apisettings (internal)
