| Field | Value |
| --- | --- |
| Title | Product Overview |
| Audience | Product stakeholders, contributors, new collaborators |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
The Adaptive Resume Generator is a desktop-first assistant that helps job seekers tailor resumes, cover letters, and application follow up at scale. This overview captures the value proposition, the audiences we serve, and the roadmap that keeps the product grounded in user outcomes while preparing for a future hosted experience.

## Key Takeaways
- Focuses on job seekers and coaches who need repeatable, high-quality tailoring instead of one-off manual edits.
- Couples structured career data with AI-assisted guidance so recommendations stay personal while respecting human oversight.
- Ships today as an offline PyQt6 application, but each service is designed to migrate to web clients and APIs without rework.

## Details
### Vision and Outcomes
The product exists to close the gap between generic resume builders and bespoke coaching. It stores a rich career history, applies NLP-driven matching against job descriptions, and outputs polished, ATS-friendly PDFs. Application tracking completes the loop so users can measure the impact of every tailored submission.

### Target Audiences
- **Primary Job Seeker:** Maintains experiences, accomplishments, and templates inside the app and expects quick turnaround when new postings arrive.
- **Career Coach / Recruiter:** Manages multiple candidates, needs consistent structure, and shares workflows that scale across clients.
- **Future API Consumers:** Will embed our intelligence pipeline within their own tooling once we expose service interfaces over HTTP.

### Core Capabilities
1. **Profile Management:** Structured storage for personal details, education, certifications, skills, and accomplishments with ordering controls.
2. **Experience Matching:** NLP routines compare bullet points to new job postings, score relevance, and suggest the best talking points.
3. **Guided AI Sessions:** Facilitated writing sessions keep humans in charge of tone and accuracy while leveraging large language model suggestions.
4. **Document Generation:** ReportLab-backed export ensures PDFs stay machine-readable, branded, and ready for applicant tracking systems.
5. **Application Tracking:** Logs each submission with follow-up reminders, enabling data-driven coaching conversations.

### Delivery Roadmap
- **Current Milestone:** Complete the desktop MVP with PyQt6 UI, local SQLite persistence, and seeded taxonomies for intelligent matching.
- **Near-Term Enhancements:** Expand bullet suggestion models, deepen analytics inside the tracker, and expose configuration for resume templates.
- **Future Evolution:** Transition to a hosted web deployment on PostgreSQL and surface REST APIs so partners can integrate the resume intelligence pipeline.

## Next Steps
- Walk through the [AI Session Guide](ai_session_guide.md) to see how humans and AI collaborate during tailoring sessions.
- Review the [System Architecture](../architecture/system_architecture.md) to understand how the product is implemented end-to-end.
