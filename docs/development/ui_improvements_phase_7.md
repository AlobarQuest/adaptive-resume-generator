# Phase 7: UI/UX Improvements - 11 Issue Resolution

**Status**: In Progress
**Started**: 2025-01-18
**Estimated Completion**: 5-7 hours

## Overview

This phase addresses 11 UI/UX issues identified by user testing. Issues range from window sizing to navigation improvements.

## Implementation Plan

### Phase 1: Window Sizing & Layout (Issues 1, 5, 10, 11)
**Status**: In Progress
**Estimated Time**: 1-2 hours

#### Issue 1: Window Sizing & Resizability ✅
- **Problem**: Main window too tall for screen, not resizable/scrollable
- **Solution**:
  - Set default window size to 1200x800
  - Make window resizable with minimum size constraints
  - Add scroll areas to tall content screens
  - Save/restore window geometry in settings
- **Files**: `src/adaptive_resume/gui/main_window.py`
- **Implementation Notes**:
  - Use `setGeometry()` to set initial size/position
  - Use `setMinimumSize()` to prevent too-small windows
  - Use `QScrollArea` for screens with dynamic content height
  - Use `QSettings` to persist window geometry

#### Issue 5: Profile Management Button Sizes
- **Problem**: "Edit Profile" button much bigger than "Import/Update from Resume"
- **Solution**: Set equal widths on both buttons
- **Files**: Need to locate Profile Management screen (may be in main_window or separate screen)
- **Status**: Pending - need to find Profile Management UI

#### Issue 10: Remove Dashboard Link
- **Problem**: Duplicate "Upload Job Posting" link at top
- **Solution**: Remove link from dashboard header
- **Files**: `src/adaptive_resume/gui/screens/dashboard_screen.py`
- **Status**: Pending

#### Issue 11: Reorder Menu
- **Problem**: Profile Management should be at bottom above Settings
- **Solution**: Reorder navigation menu items
- **Files**: `src/adaptive_resume/gui/main_window.py` (navigation setup)
- **Status**: Pending

---

### Phase 2: Profile Management Screen Enhancements (Issues 2, 3, 4)
**Status**: Not Started
**Estimated Time**: 2-3 hours

#### Issue 2: Move Education/Skills Management
- **Problem**: Education and Skills need to be in Profile Management screen
- **Solution**:
  - Create/enhance Profile Management screen with tabs or sections
  - Include Skills list with Add/Edit/Delete
  - Include Education list with Add/Edit/Delete
- **Files**: Create `src/adaptive_resume/gui/screens/profile_management_screen.py`
- **Design Decision**: Use tabbed interface (Profile | Skills | Education)

#### Issue 3: Single-Click Edit
- **Problem**: Must click record then Edit button (two-step)
- **Solution**:
  - Connect `itemDoubleClicked` signal to edit handler
  - Double-click opens edit dialog directly
- **Files**: Skills/Education list widgets
- **Implementation**: `table.itemDoubleClicked.connect(self._on_edit_item)`

#### Issue 4: Delete Button in Edit Dialogs
- **Problem**: No delete option in skill/education edit dialogs
- **Solution**:
  - Add "Delete" button to dialog alongside Save/Cancel
  - Show confirmation dialog before deletion
  - Close dialog after successful deletion
- **Files**: Skill and Education edit dialogs

---

### Phase 3: Skill Autocomplete Fix (Issue 6)
**Status**: Not Started
**Estimated Time**: 1 hour

#### Issue 6: Autocomplete Not Populating Field
- **Problem**: Clicking autocomplete suggestion doesn't fill Skill Name field, typing is blocked
- **Solution**:
  - Debug QCompleter signal connections
  - Ensure `activated` signal populates line edit
  - Check if line edit is read-only or disabled incorrectly
- **Files**: `src/adaptive_resume/gui/widgets/skill_autocomplete_widget.py` or Add Skill dialog
- **Investigation Needed**: Find where SkillAutocompleteWidget is used in Add Skill workflow

---

### Phase 4: Dashboard Improvements (Issue 7)
**Status**: Not Started
**Estimated Time**: 1 hour

#### Issue 7: Update Dashboard Bottom Boxes
- **Problem**: Need different quick action boxes
- **Solution**:
  - Box 1: "Upload Existing Resume" → opens Resume Import Dialog
  - Box 2: "Add Job Posting" → opens Upload Job Posting screen
  - Update labels, icons, click handlers
- **Files**: `src/adaptive_resume/gui/screens/dashboard_screen.py`

---

### Phase 5: Upload Job Posting Screen Cleanup (Issues 8, 9)
**Status**: Not Started
**Estimated Time**: 30 minutes

#### Issue 8: Remove Profile Selector ✅
- **Problem**: "Select Profile" dropdown not needed (single-user app)
- **Solution**: Remove profile selector widget from layout
- **Files**: `src/adaptive_resume/gui/screens/job_posting_screen.py`

#### Issue 9: Update Button Text ✅
- **Problem**: Button text unclear
- **Solution**: Change to "Analyze Job/Generate Tailored Resume"
- **Files**: `src/adaptive_resume/gui/screens/job_posting_screen.py`

---

## Implementation Order

1. ✅ Phase 1 (Issues 1, 5, 10, 11) - Window sizing and layout
2. Phase 5 (Issues 8, 9) - Upload Job Posting cleanup
3. Phase 3 (Issue 6) - Skill autocomplete fix
4. Phase 4 (Issue 7) - Dashboard improvements
5. Phase 2 (Issues 2, 3, 4) - Profile Management enhancements

---

## Testing Checklist

- [ ] Window opens at 1200x800 on first launch
- [ ] Window can be resized down to minimum size
- [ ] Window geometry persists across sessions
- [ ] Screens with tall content are scrollable
- [ ] Profile Management buttons are equal width
- [ ] Dashboard has no duplicate job posting link
- [ ] Profile Management is at bottom of menu above Settings
- [ ] Upload Job Posting has no profile selector
- [ ] Button text reads "Analyze Job/Generate Tailored Resume"
- [ ] Profile Management screen has Skills and Education tabs
- [ ] Double-clicking skill/education opens edit dialog
- [ ] Delete buttons in edit dialogs work with confirmation
- [ ] Skill autocomplete populates field when suggestion clicked
- [ ] Dashboard bottom boxes navigate correctly

---

## Key Files

### Main Window & Navigation
- `src/adaptive_resume/gui/main_window.py` - Main window, navigation menu

### Screens
- `src/adaptive_resume/gui/screens/dashboard_screen.py` - Dashboard
- `src/adaptive_resume/gui/screens/job_posting_screen.py` - Upload Job Posting
- `src/adaptive_resume/gui/screens/profile_management_screen.py` - Profile Management (may need to create)

### Dialogs
- `src/adaptive_resume/gui/dialogs/skill_edit_dialog.py` - Skill editing (need to find)
- `src/adaptive_resume/gui/dialogs/education_edit_dialog.py` - Education editing (need to find)

### Widgets
- `src/adaptive_resume/gui/widgets/skill_autocomplete_widget.py` - Skill autocomplete

---

## Progress Log

### 2025-01-18

#### Completed
- ✅ Issue 1: Window sizing and resizability (setGeometry 1200x800, setMinimumSize 1000x600)
- ✅ Issue 11: Navigation menu reordered (Profile Management moved above Settings)
- ✅ Issue 8: Removed profile selector from Upload Job Posting screen
- ✅ Issue 9: Updated button text to "Analyze Job/Generate Tailored Resume"
- ✅ Issue 10: Removed "Upload Job Posting" link from Dashboard hero
- ✅ Issue 7: Updated Dashboard bottom boxes (Upload Resume + Add Job Posting)

#### In Progress
- Working on remaining issues 2-6

#### Still To Do
- Issue 5: Profile Management button sizes
- Issue 2: Move Education/Skills to Profile Management screen
- Issue 3: Single-click edit for skills/education
- Issue 4: Delete buttons in edit dialogs
- Issue 6: Fix skill autocomplete
