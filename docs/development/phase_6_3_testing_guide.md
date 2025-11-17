# Phase 6.3: Application Tracking System - Testing Guide

## Overview

This guide provides comprehensive testing instructions for the Phase 6.3 Application Tracking System implementation. Use this guide to verify all functionality works correctly end-to-end.

## Prerequisites

Before testing, ensure:
- ✅ Database migration 49cc1707d9b9 has been applied: `alembic current`
- ✅ All 565 unit tests pass: `pytest tests/unit/ -k "not gui"`
- ✅ A profile exists in the system for testing

## Test Scenarios

### Scenario 1: Navigation Integration

**Objective**: Verify the Applications screen is accessible from main navigation

**Steps**:
1. Launch the application: `python -m adaptive_resume.main`
2. Verify the navigation menu shows "📝 Track Applications" item
3. Click on "Track Applications"
4. Verify the ApplicationsScreen loads with 3 tabs: Kanban Board, List View, Analytics

**Expected Result**:
- Navigation item is visible
- Screen loads without errors
- All 3 tabs are present and functional

---

### Scenario 2: Add New Application (Quick Entry)

**Objective**: Test quick application entry workflow

**Steps**:
1. Navigate to Track Applications screen
2. Click "+ New Application" button
3. In AddApplicationDialog:
   - Enter company: "Google"
   - Enter position: "Senior Software Engineer"
   - Enter URL: "https://careers.google.com/jobs/123"
   - Select status: "Discovered"
   - Select priority: "High"
   - Enter location: "Mountain View, CA"
   - Enter salary: "$150k-$200k"
   - Paste job description (any text)
4. Click "Create Application"

**Expected Result**:
- Confirmation message appears
- Dialog closes
- New application appears in Kanban "Discovered" column
- Application appears in List View table

---

### Scenario 3: View/Edit Application Details

**Objective**: Test comprehensive detail view and editing

**Steps**:
1. From List View, double-click on the Google application
2. ApplicationDetailDialog opens with 6 tabs
3. **Basic Info Tab**:
   - Verify all fields populated correctly
   - Change priority to "Medium"
   - Update job description
4. **Timeline Tab**:
   - Set "Discovered" date to today
5. **Contacts Tab**:
   - Add contact person: "Jane Recruiter"
   - Add contact email: "jane@google.com"
6. **Notes Tab**:
   - Add notes: "Found via LinkedIn. Reached out to recruiter."
7. Click "Save Changes"

**Expected Result**:
- All fields save correctly
- Priority badge updates in Kanban/List views
- Notes are timestamped
- Changes persist after closing dialog

---

### Scenario 4: Application Status Progression

**Objective**: Test full application lifecycle tracking

**Steps**:
1. Select the Google application
2. Progress through statuses sequentially:

   **Step 4a: Mark as Applied**
   - Open detail dialog
   - Change status to "Applied"
   - Verify application_date auto-sets to today
   - Add application method: "company_site"
   - Save

   **Step 4b: Add First Interview**
   - Open detail dialog → Interviews tab
   - Click "+ Add Interview"
   - Set date: 7 days from now
   - Set type: "phone_screen"
   - Add notes: "Initial screening with recruiter"
   - Save
   - Verify interview_count = 1
   - Verify status auto-changes to "Interview"
   - Verify first_response_date is set

   **Step 4c: Add Multiple Interviews**
   - Add technical interview (14 days from now)
   - Add onsite interview (21 days from now)
   - Verify interview_count = 3
   - Verify all interviews show in table

   **Step 4d: Receive Offer**
   - Change status to "Offer Received"
   - Verify offer_date auto-sets
   - Add salary negotiation notes

   **Step 4e: Accept Offer**
   - Change status to "Accepted"
   - Verify acceptance_date auto-sets
   - Verify total_time_to_outcome_days is calculated

**Expected Result**:
- Each status transition auto-sets appropriate dates
- Metrics calculate correctly (response_time_days, total_time_to_outcome_days)
- Interview count tracks accurately
- Application moves to correct Kanban column at each step

---

### Scenario 5: Follow-Up Tracking

**Objective**: Test follow-up scheduling and notifications

**Steps**:
1. Create a new application: "Microsoft - Software Engineer"
2. Set status to "Applied"
3. Open detail dialog
4. Schedule follow-up for yesterday (past due)
5. Save and close
6. Verify "⚠️ Follow-up due" appears on application card
7. Schedule new follow-up for 7 days from now
8. Verify warning disappears

**Expected Result**:
- Past due follow-ups show warning indicator
- Future follow-ups don't show warning
- Follow-up dates display correctly in detail view

---

### Scenario 6: Kanban Board Functionality

**Objective**: Test Kanban board visualization

**Steps**:
1. Create 5 applications with different statuses:
   - 2 x "Discovered"
   - 1 x "Applied"
   - 1 x "Interview"
   - 1 x "Offer Received"
2. Verify each column shows correct count
3. Verify cards display:
   - Company name (bold)
   - Position title
   - Priority badge (color-coded)
   - Days since application
   - Interview count (if any)
   - Follow-up warning (if applicable)
4. Double-click card to open detail dialog

**Expected Result**:
- All 9 status columns visible
- Cards distribute to correct columns
- Count badges update accurately
- Cards are visually distinct with proper styling

---

### Scenario 7: List View & Filtering

**Objective**: Test table view and filtering capabilities

**Steps**:
1. Switch to List View tab
2. Verify table shows all applications with columns:
   - Company, Position, Status, Priority, Applied Date, Days, Interviews, Actions
3. Test filters:
   - **Status filter**: Select "Applied" → verify only applied apps show
   - **Priority filter**: Select "High" → verify only high priority apps show
   - **Active Only checkbox**: Uncheck → verify accepted/rejected apps show
   - **Search**: Type "Google" → verify only Google applications show
4. Test sorting by clicking column headers
5. Test Actions menu (⋮):
   - View Details
   - Edit
   - Delete

**Expected Result**:
- All filters work independently and in combination
- Sorting works for all columns
- Search filters in real-time
- Actions menu provides quick access to operations

---

### Scenario 8: Analytics Dashboard

**Objective**: Test analytics calculations and visualization

**Steps**:
1. Create test dataset:
   - 10 total applications
   - 7 active (various statuses)
   - 2 offers received
   - 1 accepted
   - 2 rejected
2. Switch to Analytics tab
3. Verify statistics:
   - Total Applications: 10
   - Active: 7
   - Offers: 2
   - Accepted: 1
   - Offer Rate: 20% (2/10)
   - Acceptance Rate: 50% (1/2)
4. Verify conversion funnel shows counts for each status
5. Add response time data to 5 applications
6. Verify Avg Response Time calculates correctly
7. Add interviews to applications
8. Verify Avg Interviews calculates correctly

**Expected Result**:
- All metrics display correct values
- Percentages calculate accurately
- Funnel visualization shows all status counts
- Averages calculate correctly (only from applicable records)

---

### Scenario 9: Integration with Job Posting Upload

**Objective**: Test creating application from uploaded job posting

**Steps**:
1. Navigate to "Upload Job Posting" screen
2. Upload a job posting (PDF/DOCX/TXT)
3. After analysis completes, navigate to "Track Applications"
4. Click "+ New Application"
5. Verify AddApplicationDialog can be created from JobPosting:
   - Company pre-filled from posting
   - Position pre-filled from posting
   - Description pre-filled from raw_text
   - Status defaults to "Interested"

**Expected Result**:
- Job posting data pre-populates correctly
- User can create application immediately after upload
- Created application links to job_posting_id
- Tailored resume can later link to application

---

### Scenario 10: Profile Switching

**Objective**: Test applications filter by profile

**Steps**:
1. Create applications for Profile #1
2. Switch to different profile (Profile #2)
3. Verify Applications screen shows empty state
4. Create applications for Profile #2
5. Switch back to Profile #1
6. Verify original applications reappear

**Expected Result**:
- Applications correctly filtered by current profile
- No cross-profile data leakage
- Screen refreshes when profile changes

---

### Scenario 11: Delete Application

**Objective**: Test application deletion

**Steps**:
1. Create a test application
2. From List View, click Actions (⋮) → Delete
3. Confirm deletion
4. Verify application removed from all views:
   - Kanban board
   - List table
   - Analytics counts updated

**Expected Result**:
- Confirmation dialog appears
- Application deleted from database
- All views update immediately
- Analytics recalculate

---

### Scenario 12: Bulk Operations

**Objective**: Test creating multiple applications

**Steps**:
1. Click "+ New Application" 10 times
2. Create applications with varying:
   - Companies (Google, Microsoft, Amazon, Meta, Apple)
   - Priorities (High, Medium, Low)
   - Statuses (Discovered, Interested, Applied, etc.)
3. Verify all applications:
   - Appear in correct Kanban columns
   - Show in List View
   - Included in Analytics

**Expected Result**:
- System handles multiple applications without performance degradation
- All views remain responsive
- Data integrity maintained

---

### Scenario 13: Edge Cases

**Objective**: Test boundary conditions and error handling

**Steps**:

**13a: Empty State**
- Navigate to Applications with no applications created
- Verify friendly empty state message

**13b: Missing Required Fields**
- Try creating application without company name
- Verify validation error
- Try creating without position title
- Verify validation error

**13c: Invalid Dates**
- Set application_date in future
- Set offer_date before application_date
- Verify system handles gracefully

**13d: Very Long Text**
- Enter 10,000 character job description
- Verify system handles without crashing
- Verify text displays properly (truncated/scrollable)

**13e: Special Characters**
- Enter company with special chars: "ABC & Co., Inc."
- Enter position with Unicode: "Software Engineer – Backend"
- Verify displays correctly

**Expected Result**:
- Validation prevents invalid data entry
- System gracefully handles edge cases
- No crashes or data corruption
- User-friendly error messages

---

## Automated Test Verification

Verify automated tests pass:

```bash
# Run all application tracking service tests
pytest tests/unit/test_application_tracking_service.py -v

# Expected: 36 tests passing
```

Test coverage breakdown:
- ✅ Application CRUD (8 tests)
- ✅ Status Management (8 tests)
- ✅ Interview Management (4 tests)
- ✅ Contact Management (3 tests)
- ✅ Querying/Filtering (7 tests)
- ✅ Analytics/Metrics (6 tests)

---

## Performance Benchmarks

Expected performance targets:

| Operation | Target Time |
|-----------|-------------|
| Load Applications screen | < 500ms |
| Load 100 applications | < 1s |
| Filter applications | < 100ms |
| Open detail dialog | < 200ms |
| Save application | < 300ms |
| Calculate analytics | < 500ms |
| Switch Kanban/List view | < 100ms |

---

## Known Limitations

Current implementation limitations:
1. No drag-and-drop between Kanban columns (status must be changed via dialog)
2. Search only filters company/position, not full-text search of description
3. No export functionality (CSV/Excel export not yet implemented)
4. No email reminders for follow-ups (manual check required)
5. Analytics are real-time calculated (no caching for large datasets)

---

## Reporting Issues

When reporting issues, include:
- Scenario number from this guide
- Step number where failure occurred
- Expected vs actual behavior
- Screenshots if applicable
- Browser/OS information
- Database state (number of profiles, applications)

---

## Success Criteria

Phase 6.3 is considered complete when:
- ✅ All 13 test scenarios pass without errors
- ✅ All 36 automated tests pass
- ✅ Navigation integration works correctly
- ✅ Profile switching filters applications properly
- ✅ All CRUD operations work correctly
- ✅ Analytics calculate accurately
- ✅ No performance degradation with 100+ applications
- ✅ No data integrity issues or crashes

---

## Next Steps

After Phase 6.3 verification:
1. Gather user feedback on UI/UX
2. Consider implementing remaining Phase 6 features:
   - 6.1: Advanced Skill Database & Autocomplete
   - 6.4: AI-Powered Cover Letter Generation (already complete!)
   - 6.5: Job Search Integration (already complete!)
3. Optimize performance for large datasets (1000+ applications)
4. Implement advanced features (export, reminders, drag-and-drop)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-16
**Author**: Claude Code
**Status**: Ready for Testing
