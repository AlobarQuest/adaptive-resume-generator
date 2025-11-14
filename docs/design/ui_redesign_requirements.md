# UI/UX Redesign Requirements

**Date:** November 13, 2025  
**Status:** Requirements Gathering  
**Target Phase:** Post-Phase 3.5 Polish

---

## Current State Assessment

### Known Issues

#### 1. Profile List Sidebar - Too Large for Typical Use
**Current Behavior:**
- Left sidebar showing profile list
- Takes up ~25% of horizontal screen space
- Always visible

**Problem:**
- Most users will have only 1-3 profiles
- Wasting valuable screen real estate
- Makes main content area feel cramped

**User's Desired Change:**
- Move profile selection to menu (File > Select Profile)
- Show small dialog to choose/create/edit profiles
- Display current profile name in window title or status bar
- Reclaim that screen space for content

---

#### 2. General Layout Feels Confusing
**User's Concern:**
"The look and feel is a bit confusing in general"

**Questions to Help Define This:**
1. What specific part feels most confusing?
   - [ ] Too many panels visible at once?
   - [ ] Unclear what actions are available?
   - [ ] Don't know where to start?
   - [ ] Hard to find specific features?
   - [ ] Other: ___________

2. When you open the app, what do you want to see first?
   - [ ] Just a list of your jobs
   - [ ] Dashboard with quick stats
   - [ ] Most recent job details
   - [ ] Resume preview
   - [ ] Something else: ___________

3. What do you use the app for most often? (Rank 1-5)
   - ___ Adding/editing job experiences
   - ___ Enhancing bullet points
   - ___ Managing skills
   - ___ Viewing/organizing all my data
   - ___ Other: ___________

---

## Screenshots Needed

To help redesign effectively, please provide screenshots of:

1. **Main window on startup** - What you see when you first open the app
2. **Profile list sidebar** - The specific area you want to change
3. **Typical working view** - How the app looks when you're actively using it
4. **Any confusing areas** - Specific parts that feel unclear

**How to provide:**
- Save screenshots to: `docs/design/screenshots/`
- Name them descriptively: `01-main-window.png`, `02-profile-sidebar.png`, etc.

---

## Proposed Solutions (To Be Refined)

### Solution 1: Remove Profile Sidebar, Use Menu Instead

**Implementation:**
```
Before:
[Profile List Sidebar 25%] | [Main Content 75%]

After:
[Main Content 100%]
+ File menu: "Select Profile..." opens small dialog
+ Window title shows: "Adaptive Resume Generator - [Profile Name]"
```

**Benefits:**
- 25% more space for job list and content
- Cleaner, less cluttered interface
- Standard application pattern (like many IDEs)

**Implementation Steps:**
1. Create ProfileSelectorDialog (simple list + buttons)
2. Remove profile_list from MainWindow left panel
3. Add "File > Select Profile" menu item
4. Add profile name to window title
5. Load last-used profile on startup

**Estimated Effort:** 2-3 hours

---

### Solution 2: [To Be Determined Based on Your Feedback]

**What specific confusion do you experience?**
- Please describe: ___________

**What would make it clearer?**
- Your idea: ___________

---

## Your Workflow Questions

Help me understand your typical use:

1. **When you open the app, what's your first action?**
   - ___________

2. **What do you do most frequently?**
   - ___________

3. **What features do you rarely use?**
   - ___________

4. **If you could change one thing about the layout, what would it be?**
   - ___________

5. **What apps have layouts you like? (for inspiration)**
   - ___________

---

## Next Steps

1. **You:** Fill in the questions above and provide screenshots
2. **You:** Describe any other confusing aspects in plain language
3. **Claude:** Review your feedback and propose specific redesign
4. **Claude:** Create mockups/wireframes if needed
5. **Both:** Iterate until design feels right
6. **Claude:** Implement the changes
7. **You:** Test and provide feedback

---

## Communication Tips

When describing UI issues, these details help:

### Good Examples:
✅ "The profile list takes up too much space - I only have 2 profiles"
✅ "I never know where to find the enhance bullet feature"
✅ "The skills panel and education panel side-by-side is confusing - I only look at one at a time"

### Less Helpful:
❌ "It just doesn't feel right"
❌ "Make it better"
❌ "Like other apps"

### Best Approach:
1. Point to specific area: "The left sidebar with profiles..."
2. Explain the problem: "...takes up too much space for just 1-2 profiles"
3. Suggest improvement: "...move to a menu item instead"

---

## References

- **Current GUI Framework:** PyQt6 (see ADR-0003)
- **Main Window Code:** `src/adaptive_resume/gui/main_window.py`
- **Styling:** `src/adaptive_resume/gui/styles.py`
- **Views:** `src/adaptive_resume/gui/views/`

---

## Notes

Once you've filled this out, we can:
- Create mockups of proposed changes
- Prioritize which changes to make first
- Implement incrementally (one improvement at a time)
- Test each change before moving to the next

This ensures we don't break working functionality while improving the UX.
