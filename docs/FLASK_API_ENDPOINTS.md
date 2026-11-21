# Flask API Endpoints - Complete Reference

## Base URL
- Development: `http://localhost:5000`
- Environment Variable: `EXPO_PUBLIC_API_URL`

---

## Authentication Routes (`/api/auth`)

### Login
- **POST** `/api/auth/login`
- Body: `{ email: string, password: string }`
- Returns: `{ user_id, email, token }`

### Register
- **POST** `/api/auth/register`
- Body: `{ email: string, password: string, username: string }`
- Returns: `{ user_id, email, token }`

### Logout
- **POST** `/api/auth/logout`
- Auth Required: Yes
- Returns: `{ success: boolean }`

---

## Profile Routes (`/api/profile`)

### Get User Profile
- **GET** `/api/profile/<user_id>`
- Auth Required: No
- Returns: Full profile with:
  - `net_worth`, `monthly_income`, `credit_score`
  - `liabilities`, `assets`, `jobs`, `rental`
  - `lifestyle_items` (array with `image_url` support)

### Get Current User Profile
- **GET** `/api/profile/me`
- Auth Required: Yes
- Returns: Full profile of authenticated user

### Update Profile
- **PUT** `/api/profile/<user_id>`
- Auth Required: Yes (must be own profile)
- Body: Partial profile update object
- Returns: Updated profile

---

## Asset Routes (`/api/assets`)

### Get Available Assets
- **GET** `/api/assets`
- Query Params: `category` (optional: real_estate, stocks, crypto, business, investments, luxury)
- Returns: Array of assets with:
  - `id`, `name`, `category`, `price`
  - `description`, `risk_level` (low|medium|high)
  - `monthly_income` (optional), `image_url` (optional)

### Purchase Asset
- **POST** `/api/assets/purchase`
- Auth Required: Yes
- Body: `{ asset_id: string, quantity: number }`
- Returns: 
  - Success: `{ success: true, asset_id, quantity, total_cost, new_balance }`
  - Error: `{ success: false, error: string, message: string }`
- Error Codes:
  - `ASSET_NOT_FOUND` (404)
  - `INSUFFICIENT_FUNDS` (400)
  - `MISSION_CONSTRAINT_VIOLATION` (403)

### Get User Assets
- **GET** `/api/assets/portfolio`
- Auth Required: Yes
- Returns: Array of user's owned assets with current values

### Sell Asset
- **POST** `/api/assets/sell`
- Auth Required: Yes
- Body: `{ asset_id: string, quantity: number }`
- Returns: `{ success: true, asset_id, quantity, proceeds, new_balance }`

---

## Job Routes (`/api/jobs`)

### Get Available Jobs
- **GET** `/api/jobs/available`
- Returns: Array of job listings with:
  - `id`, `title`, `company`, `salary`
  - `description`, `requirements`

### Apply for Job
- **POST** `/api/jobs/apply`
- Auth Required: Yes
- Body: `{ job_id: string }`
- Returns: 
  - Success: `{ success: true, job_id, title, salary, new_balance }`
  - Error: `{ success: false, error: string, message: string }`
- Error Codes:
  - `JOB_NOT_FOUND` (404)
  - `JOB_LIMIT_REACHED` (400) - Max 2 jobs
  - `ALREADY_EMPLOYED` (400)

### Get Current Jobs
- **GET** `/api/jobs/current`
- Auth Required: Yes
- Returns: Array of user's current jobs

### Quit Job
- **POST** `/api/jobs/quit`
- Auth Required: Yes
- Body: `{ job_id: string }`
- Returns: `{ success: true, job_id, title }`

---

## Rental Routes (`/api/rentals`)

### Get Available Properties
- **GET** `/api/rentals/available`
- Returns: Array of rental properties with:
  - `id`, `name`, `monthly_rent`
  - `description`, `amenities`, `image_url`

### Rent Property
- **POST** `/api/rentals/rent`
- Auth Required: Yes
- Body: `{ property_id: string }`
- Returns:
  - Success: `{ success: true, rental_id, property_name, monthly_rent, new_balance }`
  - Error: `{ success: false, error: string, message: string }`
- Error Codes:
  - `PROPERTY_NOT_FOUND` (404)
  - `ALREADY_RENTING` (400)
  - `INSUFFICIENT_FUNDS` (400)

### Get Current Rental
- **GET** `/api/rentals/current`
- Auth Required: Yes
- Returns: Current rental details or null

### Move Out
- **POST** `/api/rentals/moveout`
- Auth Required: Yes
- Returns: `{ success: true, property_id }`

---

## Education Routes (`/api/education`)

### Get Available Courses
- **GET** `/api/education/courses`
- Returns: Array of courses with:
  - `id`, `title`, `cost`, `duration_weeks`
  - `description`, `income_boost_percentage`

### Enroll in Course
- **POST** `/api/education/enroll`
- Auth Required: Yes
- Body: `{ course_id: string }`
- Returns:
  - Success: `{ success: true, course_id, title, cost, new_balance }`
  - Error: `{ success: false, error: string, message: string }`
- Error Codes:
  - `COURSE_NOT_FOUND` (404)
  - `ALREADY_ENROLLED` (400)
  - `INSUFFICIENT_FUNDS` (400)

### Get Enrolled Courses
- **GET** `/api/education/enrolled`
- Auth Required: Yes
- Returns: Array of enrolled courses with progress

### Complete Course
- **POST** `/api/education/complete`
- Auth Required: Yes
- Body: `{ course_id: string }`
- Returns: `{ success: true, course_id, income_boost }`

---

## Mission Routes (`/api/missions`)

### Get Available Missions
- **GET** `/api/missions/available`
- Auth Required: Yes
- Returns: Array of missions with:
  - `id`, `title`, `description`, `difficulty`
  - `reward`, `constraints` (object with multipliers and restrictions)
  - `decision_points`, `success_criteria`

### Get Active Mission
- **GET** `/api/missions/active`
- Auth Required: Yes
- Returns: Current mission or null

### Start Mission
- **POST** `/api/missions/start`
- Auth Required: Yes
- Body: `{ mission_id: string }`
- Returns: `{ success: true, mission_id, constraints }`

### Complete Mission
- **POST** `/api/missions/complete`
- Auth Required: Yes
- Body: `{ mission_id: string, decision_point_ids: string[] }`
- Returns: `{ success: true, mission_id, reward, result }`

### Quit Mission
- **POST** `/api/missions/quit`
- Auth Required: Yes
- Returns: `{ success: true, mission_id }`

---

## Balance Routes (`/api/balance`)

### Get Current Balance
- **GET** `/api/balance`
- Auth Required: Yes
- Returns: `{ current_balance: number, currency: "USD" }`

### Get Balance History
- **GET** `/api/balance/history`
- Auth Required: Yes
- Query Params: `limit` (optional, default 50), `offset` (optional, default 0)
- Returns: Array of transactions with:
  - `id`, `amount`, `reason`, `timestamp`, `balance_after`

### Add Balance (Admin/Testing)
- **POST** `/api/balance/add`
- Auth Required: Yes (admin required)
- Body: `{ user_id: string, amount: number, reason: string }`
- Returns: `{ new_balance: number }`

---

## Liability Routes (`/api/liabilities`)

### Get Available Liabilities
- **GET** `/api/liabilities`
- Returns: Array of liability types with terms and rates

### Take Loan
- **POST** `/api/liabilities/loan`
- Auth Required: Yes
- Body: `{ liability_type: string, amount: number }`
- Returns: `{ success: true, loan_id, monthly_payment, total_cost }`

### Get Active Liabilities
- **GET** `/api/liabilities/active`
- Auth Required: Yes
- Returns: Array of user's current liabilities/loans

### Pay Loan
- **POST** `/api/liabilities/pay`
- Auth Required: Yes
- Body: `{ liability_id: string, amount: number }`
- Returns: `{ success: true, remaining_balance }`

---

## Lifestyle Routes (`/api/liabilities` - Lifestyle Items)

### Get Luxury Items
- **GET** `/api/liabilities/luxury`
- Returns: Array of luxury/lifestyle items with:
  - `id`, `name`, `price`, `monthly_cost`
  - `description`, `image_url`, `category`

### Purchase Lifestyle Item
- **POST** `/api/liabilities/luxury/purchase`
- Auth Required: Yes
- Body: `{ item_id: string }`
- Returns: `{ success: true, item_id, monthly_cost, new_balance }`

### Get Active Lifestyle Items
- **GET** `/api/liabilities/luxury/active`
- Auth Required: Yes
- Returns: Array of owned lifestyle items with `image_url`

---

## Loan Routes (`/api/loans`)

### Get Available Loans
- **GET** `/api/loans`
- Returns: Array of loan products with:
  - `id`, `type`, `min_amount`, `max_amount`
  - `interest_rate`, `term_months`, `monthly_payment`

### Get Active Loans
- **GET** `/api/loans/active`
- Auth Required: Yes
- Returns: Array of user's active loans with details

### Repay Loan
- **POST** `/api/loans/repay`
- Auth Required: Yes
- Body: `{ loan_id: string, amount: number }`
- Returns: `{ success: true, remaining_balance, new_balance }`

---

## Social Routes (`/api/social`)

### Get Leaderboard
- **GET** `/api/social/leaderboard`
- Query Params: `limit` (optional, default 50), `offset` (optional)
- Returns: Array of top players with:
  - `user_id`, `username`, `net_worth`, `rank`
  - `profile_picture_url`

### Get Mentors
- **GET** `/api/social/mentors`
- Query Params: `limit` (optional, default 10)
- Returns: Array of mentor profiles with expertise areas

### Follow User
- **POST** `/api/social/follow`
- Auth Required: Yes
- Body: `{ user_id: string }`
- Returns: `{ success: true, following: true }`

### Unfollow User
- **POST** `/api/social/unfollow`
- Auth Required: Yes
- Body: `{ user_id: string }`
- Returns: `{ success: true, following: false }`

### Get Followers
- **GET** `/api/social/followers/<user_id>`
- Returns: Array of follower profiles

### Get Following
- **GET** `/api/social/following/<user_id>`
- Returns: Array of followed user profiles

---

## Notification Routes (`/api/notifications`)

### Get User Notifications
- **GET** `/api/notifications`
- Auth Required: Yes
- Query Params: `limit` (optional), `offset` (optional)
- Returns: Array of notifications with:
  - `id`, `type`, `message`, `timestamp`, `read`

### Mark as Read
- **PUT** `/api/notifications/<notification_id>`
- Auth Required: Yes
- Returns: `{ success: true, read: true }`

### Get Unread Count
- **GET** `/api/notifications/unread`
- Auth Required: Yes
- Returns: `{ unread_count: number }`

---

## Error Response Format

All endpoints return errors in this format:
```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Human-readable message"
}
```

### Common Error Codes
- `UNAUTHORIZED` (401): Authentication required
- `FORBIDDEN` (403): Permission denied
- `NOT_FOUND` (404): Resource not found
- `INSUFFICIENT_FUNDS` (400): Not enough balance
- `MISSION_CONSTRAINT_VIOLATION` (403): Action blocked by mission rules
- `VALIDATION_ERROR` (400): Invalid request data
- `INTERNAL_ERROR` (500): Server error

---

## Authentication

All protected endpoints (`@require_auth` decorator) expect:
```
Authorization: Bearer <JWT_TOKEN>
```

Token obtained from login/register response and stored locally.

---

## Notes for Mobile Implementation

1. **Fractional Shares**: Stocks and crypto support decimal quantities (e.g., 0.5 shares)
2. **Image URLs**: Profile pictures, asset images, and lifestyle item images are returned via `image_url` field
3. **Decimal Precision**: All monetary values are Decimal type on backend, handle as `number` on mobile
4. **Mission Constraints**: Returned in `/api/missions/available` and `/api/missions/active`
5. **Atomic Transactions**: All financial operations are atomic (all-or-nothing)
