# UI/UX Redesign - Complete Specification

**Date:** November 13, 2025  
**Status:** Ready for Implementation  
**Based On:** User-described mockups from `Visual Look and Feel Idea/`

---

## Design Overview

**Core Pattern:** Consistent left-side navigation menu + right-side working area across all screens

```
┌──────────────┬─────────────────────────────────────────┐
│              │                                         │
│  Navigation  │        Working Area                     │
│  Menu        │        (Screen-specific content)        │
│  (Fixed)     │                                         │
│              │                                         │
└──────────────┴─────────────────────────────────────────┘
```

---

## Left Navigation Menu (All Screens)

**Fixed vertical menu on left side:**

```
┌─────────────────┐
│   App Logo      │
├─────────────────┤
│ 📊 Dashboard    │
│ 🏢 Companies    │
│    & Roles      │
│ 👤 General Info │
│ 📄 Upload Job   │
│    Posting      │
│ 📋 Review &     │
│    Print        │
├─────────────────┤
│ ⚙️  Settings    │
└─────────────────┘
```

**Implementation Notes:**
- Use QListWidget or custom buttons
- Highlight current screen
- Fixed width (~200px)
- Always visible
- Settings at bottom (separate section)

---

## Screen 1: Dashboard (Opening Screen)

### Layout

```
┌──────────────┬─────────────────────────────────────────┐
│              │  ┌───────────────────────────────────┐  │
│              │  │ Hero Image / Graphic              │  │
│  Navigation  │  │                                   │  │
│  Menu        │  │  [Upload Job Posting Button]      │  │
│              │  └───────────────────────────────────┘  │
│              │                                         │
│              │  Profile Stats:                         │
│              │  ┌─────┬─────┬─────┬─────┬─────────┐  │
│              │  │Cos  │Roles│Skill│Educ │Accomps  │  │
│              │  │  5  │ 12  │ 25  │  3  │  47     │  │
│              │  └─────┴─────┴─────┴─────┴─────────┘  │
│              │                                         │
│              │  ┌──────────────────┬────────────────┐ │
│              │  │ Quick Manage     │ Profile Info   │ │
│              │  │ Companies/Roles  │ Update         │ │
│              │  │                  │                │ │
│              │  │ [Recent items]   │ [Quick edit]   │ │
│              │  └──────────────────┴────────────────┘ │
└──────────────┴─────────────────────────────────────────┘
```

### Components

**Top Section:**
- Hero image/graphic (can be placeholder initially)
- Large "Upload Job Posting" button
  - Links to Job Posting Upload screen

**Stats Panel:**
- Display counts for:
  - Companies
  - Roles
  - Skills
  - Education entries
  - Accomplishments (total bullets across all roles)
- Grid layout, possibly with icons

**Bottom Section (Split):**
- **Left Panel:** Quick manage companies/roles
  - Recent jobs list
  - Quick add buttons
  - Links to Companies & Roles screen
  
- **Right Panel:** Profile info update
  - Key profile fields (name, contact)
  - Quick edit button
  - Links to General Info screen

---

## Screen 2: Companies and Role Management

### Layout

```
┌──────────────┬─────────────────────────────────────────┐
│              │  Companies & Roles                      │
│              │  ┌──────────────┬───────────────────┐   │
│  Navigation  │  │ Companies    │ Roles at Company  │   │
│  Menu        │  │              │                   │   │
│              │  │ • Company A  │ ┌───────────────┐ │   │
│              │  │ • Company B  │ │ Role Details  │ │   │
│              │   │ • Company C  │ │               │ │   │
│              │  │              │ │ Title:        │ │   │
│              │  │ [Add Co.]    │ │ Start Date:   │ │   │
│              │  │              │ │ End Date:     │ │   │
│              │  │              │ │ Location:     │ │   │
│              │  │              │ │               │ │   │
│              │  │              │ │ Bullets:      │ │   │
│              │  │              │ │ • ...         │ │   │
│              │  │              │ │ • ...         │ │   │
│              │  │              │ │               │ │   │
│              │  │              │ │ [Add Role]    │ │   │
│              │  │              │ │ [Enhance ✨]  │ │   │
│              │  │              │ └───────────────┘ │   │
│              │  └──────────────┴───────────────────┘   │
└──────────────┴─────────────────────────────────────────┘
```

### Components

**Left Panel (30-40%):** Companies List
- Scrollable list of companies
- Each entry shows company name
- Click to select and show roles
- "Add Company" button at bottom
- Edit/Delete actions (icons or context menu)

**Right Panel (60-70%):** Role Details
- Shows all roles for selected company
- Each role displays:
  - Job title
  - Start date / End date
  - Location
  - Description
  - **Bullet points list**
  - **"Enhance Bullet" button** (already implemented)
- "Add Role" button
- Edit/Delete actions

**Key Feature:**
- This is where the existing JobsView functionality goes
- Already has bullet enhancement working
- Just needs layout restructure

---

## Screen 3: Skills and Education

### Layout

```
┌──────────────┬─────────────────────────────────────────┐
│              │  General Info                           │
│              │                                         │
│  Navigation  │  Skills Management                      │
│  Menu        │  ┌─────────────────────────────────┐   │
│              │  │ Skill    │ Category │ Prof │ Yrs│   │
│              │  │──────────┼──────────┼──────┼────│   │
│              │  │ Python   │ Tech     │ Exp  │ 5  │   │
│              │  │ React    │ Tech     │ Adv  │ 3  │   │
│              │  │ ...      │          │      │    │   │
│              │  │                                 │   │
│              │  │ [Add Skill] [Edit] [Delete]     │   │
│              │  └─────────────────────────────────┘   │
│              │                                         │
│              │  Education & Certifications             │
│              │  ┌─────────────────────────────────┐   │
│              │  │ Degree   │ School   │ Year     │   │
│              │  │──────────┼──────────┼──────────│   │
│              │  │ BS CS    │ MIT      │ 2018     │   │
│              │  │ ...      │          │          │   │
│              │  │                                 │   │
│              │  │ [Add Education] [Edit] [Delete] │   │
│              │  └─────────────────────────────────┘   │
└──────────────┴─────────────────────────────────────────┘
```

### Components

**Top Section:** Skills Management
- Table/list showing all skills
- Columns: Skill name, Category, Proficiency, Years experience
- Add/Edit/Delete buttons
- Reuses existing SkillsPanel functionality

**Bottom Section:** Education Management
- Table/list showing education entries
- Columns: Degree, School/Institution, Graduation year, GPA
- Add/Edit/Delete buttons
- Reuses existing EducationPanel functionality

**Optional:** Certifications subsection
- Similar table for certifications
- Name, Issuer, Date obtained, Expiration

---

## Screen 4: Upload Job Posting

### Layout

```
┌──────────────┬─────────────────────────────────────────┐
│              │  Upload Job Posting                     │
│              │                                         │
│  Navigation  │  Profile: [Devon Smith      ▼]         │
│  Menu        │                                         │
│              │  ┌─────────────────────────────────┐   │
│              │  │                                 │   │
│              │  │   Drag & Drop Job Posting       │   │
│              │  │   or                            │   │
│              │  │   [Browse Files]                │   │
│              │  │   [Paste Text]                  │   │
│              │  │                                 │   │
│              │  │   Supported: .txt, .pdf, .docx  │   │
│              │  │                                 │   │
│              │  └─────────────────────────────────┘   │
│              │                                         │
│              │  [Process and Generate]                 │
│              │                                         │
└──────────────┴─────────────────────────────────────────┘
```

### Components

**Top:** Profile Selector
- Dropdown to select which profile to use
- Current profile pre-selected

**Middle:** Upload Area
- Drag-and-drop zone
- "Browse Files" button
- "Paste Text" button for copy/paste
- Supported formats: .txt, .pdf, .docx
- Visual feedback on hover/drag

**Bottom:** Action Button
- "Process and Generate" button
- Triggers job posting analysis (Phase 4)
- Shows loading state while processing

**Note:** This is Phase 4 functionality - can stub out for now

---

## Screen 5: Review and Print (Not Described Yet)

**Placeholder for Phase 5:**
- Resume template selection
- PDF preview
- Export/print controls
- Document history

---

## Settings Dialog

**Accessed from bottom of nav menu**

Already implemented - just needs to be accessible from nav menu:
- API Key management (encrypted storage)
- Enable/Disable AI enhancement toggle
- Test connection button
- Clear key option

Current implementation: `src/adaptive_resume/gui/dialogs/settings_dialog.py`

---

## Implementation Plan

### Phase 1: Core Layout Structure (4-6 hours)

**Create the main layout with navigation menu:**

1. **Create NavigationMenu widget**
   - File: `src/adaptive_resume/gui/widgets/navigation_menu.py`
   - Vertical list of menu items
   - Signal when menu item clicked
   - Highlight current screen
   - Settings button at bottom

2. **Update MainWindow**
   - Remove profile sidebar
   - Add NavigationMenu to left (fixed ~200px)
   - Add QStackedWidget for screen content
   - Create screen switching logic

3. **Create base screen classes**
   - File: `src/adaptive_resume/gui/screens/` directory
   - `DashboardScreen`
   - `CompaniesRolesScreen`
   - `GeneralInfoScreen`
   - `JobPostingScreen`
   - `ReviewPrintScreen`

### Phase 2: Dashboard Screen (3-4 hours)

1. **Hero section**
   - Placeholder image/graphic
   - Large "Upload Job Posting" button

2. **Stats panel**
   - Calculate and display counts
   - Grid layout with icons

3. **Quick manage sections**
   - Recent companies/roles list
   - Profile info summary
   - Quick action buttons

### Phase 3: Companies & Roles Screen (2-3 hours)

1. **Migrate existing JobsView**
   - Split into companies list + roles detail
   - Keep existing bullet enhancement functionality
   - Improve layout

2. **Company management**
   - Add company creation
   - Company selection
   - Company edit/delete

### Phase 4: Skills & Education Screen (2 hours)

1. **Combine existing panels**
   - SkillsPanel at top
   - EducationPanel at bottom
   - Unified layout

### Phase 5: Job Posting Screen (1 hour - stub)

1. **Create basic UI**
   - Profile selector
   - Upload area (visual only)
   - Process button (disabled for now)
   - Show "Phase 4 Coming Soon" message

### Phase 6: Settings Integration (30 min)

1. **Add Settings to nav menu**
2. **Connect to existing SettingsDialog**

### Phase 7: Polish & Testing (2-3 hours)

1. **Update styles**
2. **Add icons to menu**
3. **Improve spacing/padding**
4. **Test all workflows**

---

## Total Estimated Effort

- **Phase 1:** 4-6 hours (Core structure)
- **Phase 2:** 3-4 hours (Dashboard)
- **Phase 3:** 2-3 hours (Companies/Roles)
- **Phase 4:** 2 hours (Skills/Education)
- **Phase 5:** 1 hour (Job Posting stub)
- **Phase 6:** 30 min (Settings)
- **Phase 7:** 2-3 hours (Polish)

**Total: 14-19 hours of work**

---

## Immediate Next Steps

**Option A: Start Now (Recommended)**
- Begin Phase 1: Core layout structure
- Get the navigation menu and screen switching working
- You can test as we go

**Option B: Commit Current Work First**
- Commit the Phase 3.5 GUI integration we just finished
- Then start fresh on UI redesign

**Option C: Review & Adjust**
- You review this plan
- Make any changes
- Then we start

What would you prefer?

---

## Key Benefits

✅ **Solves your issues:**
- Removes profile sidebar (reclaims 25% space)
- Clear, consistent navigation
- One screen at a time (less confusing)
- Dedicated space for each task

✅ **Professional appearance:**
- Standard navigation pattern
- Clean, organized layout
- Room for future screens

✅ **Maintains functionality:**
- All existing features preserved
- Bullet enhancement still works
- Nothing is lost

✅ **Future-ready:**
- Easy to add Phase 4 job analysis
- Easy to add Phase 5 document generation
- Scalable architecture

Ready to proceed?
