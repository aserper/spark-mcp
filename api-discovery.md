# Spark Membership API Discovery

## Overview
- **App**: MWA JiuJitsu (`com.sparkmembership.mwajiujitsu`) v8.5.0
- **Developer**: TechElix (`com.techelix.studentapp`)
- **Base URL**: `https://mobileapi.sparkmembership.com/api/student/`
- **HTTP Client**: Retrofit + OkHttp3 + Gson
- **Auth**: Bearer token (OAuth2-style)

## Authentication

### Headers (all requests)
```
Authorization: Bearer {accessToken}
Content-Type: application/json-patch+json
Accept: application/json
```

### Token Model
```json
{
  "accessToken": "string",
  "accessTokenExpiration": "string (datetime)",
  "refreshToken": "string"
}
```

### Login Flow
1. **Validate email**: `POST auth/email/validate` — body: `{email, locationID, pushID}`
2. **Login**: `POST auth/user/login` — body: `{email, password, locationID, pushID, deviceID, OSVersion, firebaseSenderID}`
3. Response contains `AppUserEntity` with embedded `token` object
4. Token refresh: `POST auth/refresh` — body: `{accessToken, refreshToken}`

## API Endpoints

### Auth
| Method | Path | Body/Params |
|--------|------|-------------|
| POST | `auth/email/validate` | `{email, locationID, pushID}` |
| POST | `auth/user/login` | `{email, password, locationID, pushID, deviceID, OSVersion, firebaseSenderID}` |
| POST | `auth/user/register` | Map |
| POST | `auth/password/reset` | `{email, locationID}` |
| POST | `auth/password` | Map |
| POST | `auth/device` | Map |
| POST | `auth/refresh` | `{accessToken, refreshToken}` |
| POST | `auth/logout` | DeviceRequest |
| POST | `auth/location/change` | HashMap |
| GET | `auth/countries` | — |
| GET | `auth/states/{countryID}` | query: isGracie |
| GET | `auth/locations/{stateId}` | query: isGracie |
| GET | `auth/location/{ID}` | — |

### Classes / Scheduling
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `classes` | — (my classes) |
| GET | `classes/available` | query: selectedDate |
| GET | `classes/waitlist` | — |
| POST | `classes/roster/{ID}/schedule` | Map |
| POST | `classes/roster/{ID}/waitlist` | Map |
| DELETE | `classes/roster/attendee/{ID}` | body: SingleDayItem |
| POST | `classes/roster/{ID}/pickupWaitlist` | PickupCodeReqDTO |
| GET | `classes/{ID}/pickupWaitList/meta` | — |
| POST | `classes/roster/{ID}/checkin` | — |

### ClassScheduleEntity (JSON fields)
```json
{
  "classRosterID": 123,
  "classRosterName": "string",
  "rankSystemName": "string",
  "classType": "string",
  "classSizeLimit": 20,
  "classRosterDescription": "string",
  "allowAppSchedule": true,
  "enabled": true,
  "instructor": "string",
  "instructor2": "string",
  "instructor3": "string",
  "isVirtualClass": false,
  "spotsLeft": 5,
  "classFull": false,
  "utcStartTime": "datetime string",
  "utcEndTime": "datetime string",
  "fullDates": ["date1", "date2"],
  "allowToReserveRosterBeforeXMinutes": 60
}
```

### Roster / Attendance
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `roster` | — |
| GET | `roster/limit` | — |
| GET | `attendance` | query: pageIndex, pageSize |
| POST | `user/checkIn` | Map |
| POST | `user/markAbsent` | MarkAsAbsentReqDTO |

### Dashboard
| Method | Path |
|--------|------|
| GET | `dashboard` |

### User / Profile
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `settings/menu` | — |
| GET | `settings/contact` | — |
| GET | `settings/locations/active` | — |
| GET | `settings/rate` | — |
| POST | `settings/rate` | Map |
| POST | `user/picture` | Map |
| GET | `user/memberships` | — |
| POST | `user/refer` | Map |
| GET | `user/refer` | — |

### Announcements
| Method | Path |
|--------|------|
| GET | `announcement` |
| GET | `announcement/{ID}` |

### Messages
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `messages/chat` | query: pageIndex, pageSize |
| POST | `messages` | Map |
| POST | `messages/status/read` | query: messageType |

### Curriculum
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `curriculum` | — |
| GET | `curriculum/module` | query params |
| GET | `curriculum/module/lesson/{ID}` | — |
| GET | `rank/achieved` | — |

### Payments
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `payment/methods` | — |
| GET | `payment/methods/saved` | — |
| POST | `payment/method` | Map |
| GET | `payment/history` | — |
| GET | `payment/gateway` | — |
| GET | `payment/invoice/{ID}` | — |

### Checkout / Sales
| Method | Path | Body/Params |
|--------|------|-------------|
| GET | `checkoutpage` | query params |
| GET | `checkoutpage/{ID}/items` | — |
| POST | `salespage/purchase` | CreditCardInfo |
| POST | `salespage/{ID}/coupencode/validate` | Map |

## AppUserEntity (login response)
```json
{
  "token": { "accessToken": "", "accessTokenExpiration": "", "refreshToken": "" },
  "locationID": "string or int",
  "contactID": 123,
  "name": "string",
  "allowRegister": true,
  "isFranchise": false,
  "activeLocations": [...],
  "announcement": [...]
}
```

## Notes
- Email + password stored in SharedPreferences as "EMAIL" and "PASSWORD"
- Location selection required (multi-studio support)
- SSL cert verification is disabled in the app (trusts all certs)
- Timeouts: 30s connect/read/write
