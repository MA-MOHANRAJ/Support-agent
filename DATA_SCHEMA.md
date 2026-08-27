# Data Schema Documentation

This document describes the schema and field definitions for datasets stored in `data/`.

---

## 1. `tickets.json`
Array of customer support ticket records.

| Field | Type | Description |
|---|---|---|
| `ticket_id` | String | Unique ticket identifier (e.g. `TCK-10001`) |
| `account_id` | String | Foreign key reference to `accounts.json` (`account_id`) |
| `product` | String | Target product name (e.g., `DataBridge Pro`, `CloudSync`, etc.) |
| `category` | String | Issue category (`Technical Issue`, `Configuration / Setup`, `Billing / License`, etc.) |
| `priority` | String | Ticket severity (`Low`, `Medium`, `High`, `Urgent`) |
| `status` | String | Lifecycle state (`Open`, `In Progress`, `Waiting on Customer`, `Resolved`, `Closed`) |
| `sentiment` | String | Customer sentiment (`Positive`, `Neutral`, `Frustrated`, `Angry`) |
| `subject` | String | Summary headline of the problem |
| `description` | String | Full issue details, environment metadata, and logs |
| `requester` | Object | Contact info: `name`, `email`, and `role` |
| `assigned_agent` | String | Assigned support engineer name or `Unassigned` |
| `tags` | Array<String> | Search/filtering tags |
| `created_at` | String (ISO 8601) | Timestamp when ticket was opened |
| `updated_at` | String (ISO 8601) | Timestamp of latest activity |
| `resolution_time_hours` | Float \| Null | Total hours taken to resolve (null if active) |
| `satisfaction_score` | Integer (1-5) \| Null | CSAT rating if submitted |
| `resolution_summary` | String \| Null | Summary of resolution steps if closed |

---

## 2. `accounts.json`
Array of customer account summaries.

| Field | Type | Description |
|---|---|---|
| `account_id` | String | Unique account identifier (e.g. `ACC-1001`) |
| `company_name` | String | Legal organization name |
| `tier` | String | Account subscription plan (`Starter`, `Professional`, `Enterprise`) |
| `industry` | String | Industry vertical |
| `arr_usd` | Number | Annual Recurring Revenue in USD |
| `mrr_usd` | Number | Monthly Recurring Revenue in USD |
| `active_users` | Integer | Currently active user count |
| `licensed_seats` | Integer | Total licensed user capacity |
| `products_enabled` | Array<String> | List of subscribed product modules |
| `account_health_score` | Integer (1-100) | Composite account health index |
| `sla_tier` | String | SLA level (`Standard`, `Gold`, `Platinum 24x7`) |
| `csm_assigned` | String | Dedicated Customer Success Manager |
| `primary_contact` | Object | `name`, `email`, `role`, and `phone` |
| `billing_cycle` | String | Payment interval (`Annual`, `Monthly`) |
| `status` | String | Customer status (`Active`, `Past Due`, `Onboarding`, `At Risk`) |
| `created_at` | String (ISO 8601) | Account creation timestamp |
| `contract_renewal_date` | String (YYYY-MM-DD) | Upcoming contract renewal date |
