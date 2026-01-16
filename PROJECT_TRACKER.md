# Network Device Geolocation Mapper - Project Tracker

## Project Overview
A web-based application for mapping network devices to physical office locations. Designed for IT/security teams to visualize where devices are located based on subnet-to-office mappings.

**Target Users:** 5-20 engineers  
**Hosting:** IIS on internal server  
**Server Hostname:** edcv-utl-idd1  
**Data Storage:** PostgreSQL 18  
**Authentication:** None (internal network only)

## Current Status: 🔧 IN PROGRESS - Testing Office Library functionality

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Server: edcv-utl-idd1                          │
│                                                             │
│   IIS (Port 8080)                Flask API (Port 5050)      │
│   └── NetworkMapper site         ├── /api/health            │
│       └── index.html ◄──────────►├── /api/offices           │
│              │                   ├── /api/clients           │
│              │                   ├── /api/mappings          │
│         Direct API call          └── /api/devices           │
│         (CORS enabled)                    │                 │
│                                           ▼                 │
│                                  PostgreSQL 18              │
│                                  └── network_mapper_db      │
└─────────────────────────────────────────────────────────────┘
                    ▲
              Users browse to
         http://edcv-utl-idd1:8080
```

**Note:** Port 5001 was unavailable (used by Live Tenant Analyzer app), so Flask runs on port 5050.

---

## Environment Verification (2026-01-16)

| Component | Status | Details |
|-----------|--------|---------|
| Python | ✅ Verified | 3.14.2 |
| pip / Flask | ✅ Verified | Installed and working |
| flask-cors | ✅ Installed | CORS enabled for cross-origin requests |
| psycopg2-binary | ✅ Installed | PostgreSQL driver working |
| PostgreSQL | ✅ Running | Version 18, password obtained |
| PostgreSQL Database | ✅ Created | `network_mapper_db` with 4 tables |
| IIS | ✅ Running | NetworkMapper site on port 8080 |
| IIS URL Rewrite | ✅ Installed | Available but not yet configured |
| Flask API | ✅ Running | Port 5050, health check passing |
| HTML Frontend | ✅ Deployed | Connected to API successfully |

---

## File Locations (Server: edcv-utl-idd1)

| File | Location | Purpose |
|------|----------|---------|
| api_server.py | `E:\Apps\NetworkMapper\` | Flask REST API |
| config.py | `E:\Apps\NetworkMapper\` | Database password (excluded from version control) |
| index.html | `C:\inetpub\wwwroot\NetworkMapper\` | Frontend application |

---

## Feature Status

### ✅ Completed Features

| Feature | Description | Version |
|---------|-------------|---------|
| Excel Import | Parse .xlsx files, extract device IPs | v1 |
| Subnet Detection | Auto-detect unique subnets from imported data | v1 |
| Office Library (Local) | Add/edit/remove office locations | v1 |
| City Search | Local database + online fallback + manual entry | v6 |
| Subnet Mapping | Assign subnets to offices with Office/Remote type | v2 |
| Interactive Map | Leaflet.js with CartoDB dark tiles | v1 |
| Location Clustering | One marker per office showing device count | v2 |
| Device View | Individual device markers (scattered) | v2 |
| Filtering | Filter by All/Office/Remote/Unmapped | v1 |
| Sidebar | Expandable location groups with device lists | v2 |
| New Client | Clear session for new client data | v3 |
| Import Wizard | 3-step guided import process | v3 |
| Map Refresh | Fix tile loading issues without data loss | v6 |
| Export CSV | Summary report export | v1 |
| Local Backup | JSON export/import for offline backup | v6 |
| PostgreSQL Database | 4 tables created and accessible | v8 |
| Flask API | REST endpoints running on port 5050 | v8 |
| IIS Hosting | NetworkMapper site on port 8080 | v8 |
| API Connection | Frontend connecting to backend successfully | v8 |

### 🔧 In Progress (2026-01-16)

| Feature | Description | Status |
|---------|-------------|--------|
| Office Library (DB) | Add/view offices via PostgreSQL | Testing - Decimal conversion fix applied |
| Save Client | Persist client mappings to database | Ready to test |
| Load Client | Dropdown to load saved client mappings | Ready to test |
| Delete Client | Remove client data from database | Ready to test |

### 📋 Planned / Next Steps

| Feature | Description | Priority |
|---------|-------------|----------|
| IIS Reverse Proxy | Route `/api` through IIS instead of direct port | Medium |
| Flask Auto-Start | Task Scheduler to start API on server boot | High |
| Delta Import | Handle updated Excel files (add/remove devices) | Medium |
| **Atera API Integration** | Pull device data directly from Atera instead of Excel import | High (Future Phase) |

### ❌ Abandoned

| Feature | Description | Reason |
|---------|-------------|--------|
| SharePoint Integration | Store data in SharePoint Lists | JavaScript blocked in SP document viewer |

---

## 🔮 Atera Integration (Future Phase)

**Overview:** Replace Excel import with direct Atera API calls to fetch device inventory.

**Requirements:**
- Atera API key (stored in .env file on server)
- Python script to fetch devices from Atera API
- Map Atera fields to existing device schema

**Reference:** User has existing Python script for Atera API integration (to be provided)

**Data Mapping (tentative):**
| Atera Field | App Field |
|-------------|-----------|
| MachineName | name |
| IpAddresses | ip_address |
| MacAddresses | mac_address |
| DeviceType | device_type |
| Vendor | manufacturer |
| OS | os |

**Implementation Steps:**
1. ✅ Complete base application with PostgreSQL (in progress)
2. Obtain Atera API credentials
3. Create .env file for API key storage
4. Adapt existing Atera Python script for this application
5. Add "Import from Atera" option alongside Excel import

---

## PostgreSQL Database Schema

**Database:** `network_mapper_db`  
**Status:** ✅ Created with all tables

### 1. office_locations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Office name (e.g., "Merrillville Office") |
| latitude | DECIMAL(9,6) | NOT NULL | Decimal degrees (e.g., 41.482800) |
| longitude | DECIMAL(9,6) | NOT NULL | Decimal degrees (e.g., -87.332800) |
| created_at | TIMESTAMP | DEFAULT NOW() | When record was created |

### 2. clients
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Client name (e.g., "ABC Corporation") |
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
| ip_address | VARCHAR(15) | NOT NULL | Device IP (e.g., "192.168.1.100") |
| mac_address | VARCHAR(17) | | MAC address if available |
| device_type | VARCHAR(100) | | Type from Excel |
| manufacturer | VARCHAR(100) | | Device manufacturer |
| os | VARCHAR(100) | | Operating system |

---

## Tools & Dependencies

### Frontend Libraries (CDN)
| Library | Version | CDN URL | Purpose |
|---------|---------|---------|---------|
| Leaflet.js | 1.9.4 | unpkg.com/leaflet@1.9.4 | Interactive mapping |
| SheetJS (xlsx) | 0.18.5 | cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5 | Excel file parsing |

### Backend (Server: edcv-utl-idd1)
| Component | Version | Location | Purpose |
|-----------|---------|----------|---------|
| Python | 3.14.2 | System | Runtime for API server |
| Flask | Latest | pip | REST API framework |
| flask-cors | Latest | pip | CORS support |
| psycopg2-binary | Latest | pip | PostgreSQL driver |
| PostgreSQL | 18 | System | Database |
| IIS | Existing | System | Web server |

### Fonts (Google Fonts)
| Font | Use |
|------|-----|
| JetBrains Mono | Code, monospace elements |
| Inter | UI text |

### Map Tiles
| Provider | Style | URL Pattern |
|----------|-------|-------------|
| CartoDB | Dark Matter | `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png` |

### APIs
| API | Purpose | Auth | Port |
|-----|---------|------|------|
| Flask API | Data storage (CRUD operations) | None (internal network) | 5050 |
| geocode.maps.co | Online city lookup (fallback) | None (free tier) | N/A |

---

## Setup Checklist

### Server Setup (edcv-utl-idd1)
- [x] Verify Python installed (3.14.2)
- [x] Verify pip works
- [x] Install Flask (`pip install flask`)
- [x] Install flask-cors (`pip install flask-cors`)
- [x] Install psycopg2-binary (`pip install psycopg2-binary`)
- [x] Verify PostgreSQL installed (v18)
- [x] Obtain PostgreSQL credentials ✅
- [x] Create database `network_mapper_db` (via pgAdmin 4)
- [x] Run create_tables.sql (via pgAdmin 4 Query Tool)
- [x] Deploy api_server.py to `E:\Apps\NetworkMapper\`
- [x] Create config.py with DB_PASSWORD
- [x] Start Flask API on port 5050
- [ ] Configure Task Scheduler for API startup on boot

### IIS Setup
- [x] Verify IIS running
- [x] Verify URL Rewrite module installed
- [x] Create NetworkMapper site on port 8080
- [x] Deploy index.html to `C:\inetpub\wwwroot\NetworkMapper\`
- [x] Update API_BASE to `http://edcv-utl-idd1:5050/api`
- [x] Test application access - showing "Connected" ✅
- [ ] (Optional) Configure reverse proxy to use `/api` path

### Application Testing
- [x] Health check endpoint working (`/api/health`)
- [ ] Office Library - Add office (Decimal fix applied, needs retest)
- [ ] Office Library - View offices
- [ ] Office Library - Delete office
- [ ] Client Import - New client wizard
- [ ] Client Save - Persist to database
- [ ] Client Load - Retrieve from database
- [ ] Client Delete - Remove from database
- [ ] Full end-to-end test with real data

### Team Rollout
- [ ] Complete all testing
- [ ] Share URL with team (`http://edcv-utl-idd1:8080`)
- [ ] Provide quick-start guide
- [ ] Designate admin for office library management

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
| v8 | 2026-01-16 | PostgreSQL + IIS integration (in progress) |

---

## Known Issues / Bugs Found

| Issue | Status | Resolution |
|-------|--------|------------|
| Map tile loading | Known | Use Refresh Map button |
| Large Excel files | Known | Performance may degrade with 1000+ devices |
| Concurrent editing | Known | Last-write-wins (no real-time sync) |
| City database | Known | Limited to ~100 cities; use manual entry for others |
| SharePoint hosting | Abandoned | Does not work due to JS security restrictions |
| Port 5001 conflict | Resolved | Changed to port 5050 (5001 used by Live Tenant Analyzer) |
| PostgreSQL Decimal type | Fixed | Added `convert_decimals()` function in api_server.py |

---

## Lessons Learned

### SharePoint Document Hosting (2026-01-15)
SharePoint document libraries do **not** execute JavaScript properly. HTML files opened from SharePoint Documents are either:
- Shown in a preview mode that blocks JS
- Downloaded rather than executed

**Proper SharePoint custom apps require:**
- SharePoint Framework (SPFx) - complex development setup
- Power Apps - low-code but different paradigm

**Resolution:** Switched to IIS + PostgreSQL architecture on internal server.

### Port Conflicts (2026-01-16)
Always verify port availability before deployment. Port 5001 was already in use by another application (Live Tenant Analyzer).

**Resolution:** Changed Flask API to port 5050.

### PostgreSQL Decimal Type (2026-01-16)
PostgreSQL returns DECIMAL columns as Python `Decimal` objects, which are not JSON-serializable by default. Flask's `jsonify()` fails silently or throws errors.

**Resolution:** Added `convert_decimals()` helper function to convert Decimal to float before returning JSON responses.

---

## URLs & Access

| Resource | URL |
|----------|-----|
| Application | http://edcv-utl-idd1:8080 |
| API Health Check | http://edcv-utl-idd1:5050/api/health |
| API Offices | http://edcv-utl-idd1:5050/api/offices |
| API Clients | http://edcv-utl-idd1:5050/api/clients |

---

## Contacts / Resources

- **Application Server:** edcv-utl-idd1
- **Application URL:** http://edcv-utl-idd1:8080
- **API URL:** http://edcv-utl-idd1:5050/api
- **PostgreSQL:** localhost:5432 on edcv-utl-idd1
- **Database:** network_mapper_db
- **API Files:** E:\Apps\NetworkMapper\
- **Web Files:** C:\inetpub\wwwroot\NetworkMapper\
- **Leaflet Docs:** leafletjs.com/reference.html
- **SheetJS Docs:** docs.sheetjs.com
- **Flask Docs:** flask.palletsprojects.com
- **psycopg2 Docs:** psycopg.org/docs/
