# AquaPulse API Documentation

## Base URL
```
Development: http://localhost:5001
Production: https://api.aquapulse.com
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Expiry
- Access Token: 1 hour
- Refresh Token: 30 days

---

## 1. Authentication Endpoints

### POST /api/auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "role": "citizen",
  "phone": "+1234567890",
  "organization": "Water Department",
  "ward": "Ward 5",
  "address": "123 Main St"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": { user_object },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### POST /api/auth/login
Login user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": { user_object },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### POST /api/auth/refresh
Refresh access token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### GET /api/auth/me
Get current user profile. **(Protected)**

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "citizen",
    "phone": "+1234567890",
    "organization": "Water Department",
    "ward": "Ward 5",
    "is_active": true,
    "created_at": "2026-08-17T10:00:00Z"
  }
}
```

---

## 2. Monitoring Endpoints

### GET /api/monitoring/nodes
Get all monitoring nodes.

**Query Parameters:**
- None (public nodes shown to unauthenticated users)

**Response (200):**
```json
{
  "nodes": [
    {
      "id": 1,
      "name": "Main Station A",
      "location": "Central Park",
      "ward": "Ward 1",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "status": "active",
      "equipment_health": {
        "filter": {"health": 95, "status": "good"},
        "pump": {"health": 88, "status": "good"},
        "sensor": {"health": 92, "status": "good"}
      }
    }
  ],
  "total": 1
}
```

### POST /api/monitoring/nodes
Create new monitoring node. **(Admin/Government)**

**Request Body:**
```json
{
  "name": "Station B",
  "location": "North District",
  "ward": "Ward 2",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "hardware_id": "NODE-001",
  "is_public": true
}
```

### GET /api/monitoring/readings
Get readings with filters.

**Query Parameters:**
- `node_id` (optional): Filter by node
- `start_date` (optional): ISO format date
- `end_date` (optional): ISO format date
- `limit` (optional): Max results (default: 100)
- `status` (optional): Safe, Caution, Unsafe
- `anomalies_only` (optional): true/false

**Response (200):**
```json
{
  "readings": [
    {
      "id": 1,
      "node_id": 1,
      "timestamp": "2026-08-17T10:00:00Z",
      "parameters": {
        "pH": 7.2,
        "tds": 250,
        "turbidity": 1.5,
        "temperature": 25.0,
        "conductivity": 500,
        "dissolved_oxygen": 8.5
      },
      "overall_status": "Safe",
      "is_anomaly": false
    }
  ],
  "total": 1
}
```

### GET /api/monitoring/readings/stats
Get statistics for readings.

**Query Parameters:**
- `node_id` (optional): Filter by node
- `hours` (optional): Time period (default: 24)

**Response (200):**
```json
{
  "period": "Last 24 hours",
  "total_readings": 100,
  "statistics": {
    "pH": {
      "current": 7.2,
      "min": 6.8,
      "max": 7.5,
      "avg": 7.1,
      "std_dev": 0.2
    }
  },
  "anomaly_count": 2
}
```

---

## 3. Alerts Endpoints

### GET /api/alerts/
Get all alerts with filters.

**Query Parameters:**
- `node_id` (optional): Filter by node
- `severity` (optional): low, medium, high, critical
- `alert_type` (optional): contamination, anomaly, equipment, threshold
- `status` (optional): active, acknowledged, resolved, all
- `start_date` (optional): ISO format
- `end_date` (optional): ISO format
- `limit` (optional): Max results (default: 50)

**Response (200):**
```json
{
  "alerts": [
    {
      "id": 1,
      "timestamp": "2026-08-17T10:00:00Z",
      "severity": "high",
      "alert_type": "contamination",
      "message": "pH level out of safe range",
      "status": "active",
      "node_id": 1
    }
  ],
  "total": 1
}
```

### POST /api/alerts/:id/acknowledge
Acknowledge an alert. **(Admin/Government)**

**Response (200):**
```json
{
  "message": "Alert acknowledged successfully",
  "alert": { alert_object }
}
```

### POST /api/alerts/:id/resolve
Resolve an alert. **(Admin/Government)**

**Request Body:**
```json
{
  "resolution_notes": "Issue fixed by replacing filter"
}
```

**Response (200):**
```json
{
  "message": "Alert resolved successfully",
  "alert": { alert_object }
}
```

---

## 4. Citizen Portal Endpoints

### GET /api/citizen/dashboard
Get public water quality dashboard.

**Query Parameters:**
- `ward` (optional): Filter by ward

**Response (200):**
```json
{
  "overall_status": "Safe",
  "safe_nodes": 8,
  "total_nodes": 10,
  "nodes_data": [
    {
      "node": { node_object },
      "latest_reading": { reading_object }
    }
  ]
}
```

### POST /api/citizen/report-issue
Submit water quality issue. **(Protected)**

**Request Body (multipart/form-data):**
```
title: "Bad smell in water"
description: "Water has unusual odor"
category: "odor"
severity: "medium"
location: "123 Main St"
ward: "Ward 1"
latitude: 28.6139
longitude: 77.2090
photo: <file>
```

**Response (201):**
```json
{
  "message": "Issue reported successfully",
  "report": { report_object }
}
```

### GET /api/citizen/education
Get educational resources.

**Response (200):**
```json
{
  "resources": [
    {
      "title": "Understanding Water Quality Parameters",
      "description": "Learn about pH, TDS, turbidity...",
      "content": { educational_content }
    }
  ]
}
```

---

## 5. Analytics Endpoints

### GET /api/analytics/forecast
Get 24-hour forecast. **(Protected)**

**Query Parameters:**
- `node_id` (optional): Filter by node
- `parameter` (optional): Specific parameter to forecast

**Response (200):**
```json
{
  "forecast": {
    "pH": {
      "forecast": [7.2, 7.3, 7.2, ...],
      "confidence_lower": [6.8, 6.9, ...],
      "confidence_upper": [7.6, 7.7, ...]
    }
  },
  "historical_data_points": 168
}
```

### POST /api/analytics/anomaly-detection
Detect anomaly in reading. **(Protected)**

**Request Body:**
```json
{
  "pH": 4.5,
  "tds": 850,
  "turbidity": 15.0,
  "temperature": 28.0,
  "conductivity": 900,
  "dissolved_oxygen": 4.2
}
```

**Response (200):**
```json
{
  "is_anomaly": true,
  "anomaly_score": 0.85,
  "severity": "high",
  "parameters": { input_parameters }
}
```

### GET /api/analytics/predictive-maintenance
Get equipment maintenance predictions. **(Admin/Government)**

**Query Parameters:**
- `node_id` (required): Node to analyze

**Response (200):**
```json
{
  "node_id": 1,
  "node_name": "Main Station A",
  "predictions": {
    "filter": {
      "current_health": 85,
      "days_until_maintenance": 15,
      "priority": "medium",
      "recommendation": "Plan routine maintenance..."
    }
  }
}
```

### GET /api/analytics/trends
Get trend analysis. **(Protected)**

**Query Parameters:**
- `node_id` (optional): Filter by node
- `period` (optional): daily, weekly, monthly
- `months` (optional): Number of months (default: 3)

**Response (200):**
```json
{
  "trends": {
    "pH": {
      "periods": ["2026-06", "2026-07", "2026-08"],
      "mean": [7.1, 7.2, 7.2],
      "trend_direction": "stable"
    }
  }
}
```

---

## 6. Reports Endpoints

### POST /api/reports/generate/cpcb
Generate CPCB compliance report. **(Admin/Government)**

**Request Body:**
```json
{
  "start_date": "2026-07-01T00:00:00Z",
  "end_date": "2026-07-31T23:59:59Z",
  "node_id": 1
}
```

**Response (201):**
```json
{
  "message": "CPCB report generated successfully",
  "report": {
    "report_id": "CPCB-20260817-120000",
    "compliance_score": 95.5,
    "overall_status": "Fully Compliant",
    "parameters": {
      "pH": {
        "is_compliant": true,
        "compliance_percentage": 98.5
      }
    },
    "recommendations": []
  }
}
```

### POST /api/reports/generate/daily
Generate daily summary report. **(Admin/Government)**

**Request Body:**
```json
{
  "date": "2026-08-17"
}
```

### GET /api/reports/
Get all reports. **(Protected)**

**Query Parameters:**
- `type` (optional): cpcb, daily, weekly, monthly
- `start_date` (optional): Filter by generation date
- `end_date` (optional): Filter by generation date
- `limit` (optional): Max results (default: 50)

**Response (200):**
```json
{
  "reports": [
    {
      "id": 1,
      "report_id": "CPCB-20260817-120000",
      "report_type": "cpcb",
      "title": "CPCB BIS 10500:2012 Compliance Report",
      "compliance_score": 95.5,
      "generated_at": "2026-08-17T12:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/reports/:id/export
Export report. **(Protected)**

**Query Parameters:**
- `format`: csv, pdf

**Response:**
- File download

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required field: email"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Database connection failed"
}
```

---

## Rate Limiting

- **Authentication endpoints:** 5 requests per minute
- **Data retrieval:** 100 requests per minute
- **Report generation:** 10 requests per hour

---

## CPCB Standards (BIS 10500:2012)

| Parameter | Safe Range | Unit |
|-----------|------------|------|
| pH | 6.5 - 8.5 | - |
| TDS | 0 - 500 | ppm |
| Turbidity | 0 - 5 | NTU |
| Temperature | 15 - 35 | °C |
| Conductivity | 0 - 1000 | µS/cm |
| Dissolved Oxygen | 5 - 14 | mg/L |

---

## WebSocket Events

### Connect
```javascript
socket.on('connect', () => {
  console.log('Connected to AquaPulse');
});
```

### New Reading
```javascript
socket.on('new_reading', (data) => {
  console.log('New reading:', data);
});
```

### New Alert
```javascript
socket.on('new_alert', (data) => {
  console.log('New alert:', data);
});
```

---

## Support

For API support:
- Email: api-support@aquapulse.com
- Documentation: https://docs.aquapulse.com
- GitHub: https://github.com/sorathiyalaksh37-lang/AquaPulse

**Last Updated:** 2026-08-17
**API Version:** 1.0.0
