"""Source-based NASA Space Apps 2026 judging guide companion.

This module encodes the 11-page user-provided November 13, 2026 Judging &
Awards Guide. It does NOT certify eligibility or submit a project to NASA.
"""
from typing import Literal
from pydantic import BaseModel, Field

GUIDE = {
    "title": "2026 NASA Space Apps Challenge — Judging & Awards Guide",
    "guide_date": "2026-11-13",
    "basis": "User-provided 11-page Judging & Awards Guide (2026-11-13)",
    "purpose": "Collaborative learning, growth and sharing, not awards alone (p.1).",
    "challenge": "Field Shift: Adapting Farms with NASA Data",
    "submission_deadline": "2026-11-15 23:59, Local Event local time; Universal Event uses Team Owner local time (p.3).",
    "demo": {"slide_limit": 7, "video_seconds_limit": 30, "english_language": True, "subtitles_exception": "Demo videos spoken in other languages require English subtitles."},
    "scoring": {"min": 1, "max": 5, "criteria": [
        {"id": "impact", "name": "Impact", "page": 5, "question": "Who could benefit, and how significant is the problem?", "suggested_proof": "Farmer or local stakeholder validation, concrete decision supported, access and scale limits"},
        {"id": "creativity", "name": "Creativity", "page": 5, "question": "What is genuinely new or meaningfully improved?", "suggested_proof": "NASA–local input synthesis, explainable comparisons, useful 3D evidence rather than visual novelty alone"},
        {"id": "validity", "name": "Validity", "page": 6, "question": "Is the science, technical approach, and usability plausible and testable?", "suggested_proof": "Data lineage, validation gates, experimental limitations, tests, reproducible examples"},
        {"id": "relevance", "name": "Relevance", "page": 6, "question": "Does NASA data genuinely drive the solution to the chosen challenge?", "suggested_proof": "NASA POWER source records, input→comparison trace, farmer soil and priority inputs"},
        {"id": "presentation", "name": "Presentation", "page": 7, "question": "Can judges understand the problem and result quickly?", "suggested_proof": "One farmer story, a 7-slide or 30-second demo, honest caveats, complete credits"}
    ]},
    "eligibility_notes": [
        "Respond to an official NASA Space Apps challenge (p.3).",
        "All team members must be registered for the same Local or Universal Event, not waitlisted, and listed on the Members tab (p.3).",
        "Local teams require at least 1 member; Universal teams at least 2; maximum team size 6 (p.3).",
        "Complete required Project Submission fields, provide a demo, and use English (or English video subtitles) (p.3).",
        "Submit via Team page → Project tab → edit → submit before the applicable deadline (p.3).",
        "Agree to Terms/Privacy and original-work/reference/copyright declarations (p.3).",
        "NASA reviews eligibility under a China funding restriction policy (p.4). Do not infer eligibility from this app. The separate Project Submission Guide and applicable Terms may add details not in this guide."
    ],
    "global_awards": ["Best Use of Science", "Best Use of Data", "Best Use of Technology", "Galactic Impact", "Best Mission Concept", "Most Inspirational", "Best Storytelling Award", "Global Connection Award", "Art & Technology Award", "Local Impact Award"],
    "warning": "Educational readiness aid only; manually checked boxes are unverified. This does not determine eligibility or submit to NASA."
}


class SubmissionDraft(BaseModel):
    event_type: Literal["local", "universal"] = "local"
    team_size: int = Field(default=6, ge=0, le=50)
    demo_format: Literal["none", "slides", "video"] = "none"
    slide_count: int = Field(default=0, ge=0, le=100)
    video_seconds: float = Field(default=0, ge=0, le=600)
    video_spoken_english: bool = True
    video_english_subtitles: bool = False
    references: list[str] = Field(default_factory=list, max_length=200)
    registered_same_event: bool = False
    members_tab_complete: bool = False
    official_challenge: bool = False
    fields_complete: bool = False
    materials_english: bool = False
    references_verified: bool = False
    copyright_permissions_confirmed: bool = False
    originality_attested: bool = False
    terms_privacy_attested: bool = False
    submitted_on_time: bool = False


def audit_draft(draft: SubmissionDraft):
    checks = []

    def check(id: str, title: str, passed: bool, guide_page: int, evidence_type: str = "self_reported"):
        checks.append({"id": id, "title": title, "pass": bool(passed), "guide_page": guide_page,
                       "evidence_type": evidence_type})

    check("team_size", "Team size valid for chosen event", (1 if draft.event_type == "local" else 2) <= draft.team_size <= 6, 3, "structural")
    check("same_event", "Every member registered for the same event and not waitlisted", draft.registered_same_event, 3)
    check("members_tab", "All team members listed on Members tab", draft.members_tab_complete, 3)
    check("challenge", "Official challenge selected", draft.official_challenge, 3)
    check("fields", "All required submission fields complete", draft.fields_complete, 3)
    demo_ok = ((draft.demo_format == "slides" and 1 <= draft.slide_count <= 7) or
               (draft.demo_format == "video" and 0 < draft.video_seconds <= 30))
    check("demo", "Demo within 7-slide or 30-second limit", demo_ok, 3, "structural")
    check("english", "Project page and linked materials in English", draft.materials_english, 3)
    subtitle_ok = draft.demo_format != "video" or draft.video_spoken_english or draft.video_english_subtitles
    check("subtitles", "English subtitles if demo spoken in another language", subtitle_ok, 3, "structural_self_reported")
    check("references", "External resources listed and references reviewed", bool([x for x in draft.references if x.strip()]) and draft.references_verified, 3)
    check("copyright", "Rights or permissions for third-party materials confirmed", draft.copyright_permissions_confirmed, 3)
    check("originality", "Original-work declaration confirmed", draft.originality_attested, 3)
    check("terms", "Terms, Privacy Policy and required declaration acknowledged", draft.terms_privacy_attested, 3)
    check("submission", "Project submitted on time via official team Project tab", draft.submitted_on_time, 3)
    passed = sum(item["pass"] for item in checks)
    return {"status": "self_reported_checklist_only", "passed": passed, "total": len(checks),
            "checks": checks, "all_self_reported": passed == len(checks),
            "disclaimer": "NASA eligibility is NOT independently verified. Even all-green answers are only user attestations and draft-format checks.",
            "unverified": ["Official NASA account and event registration (including waitlist status)", "Submission confirmation and deadline; applicable NASA affiliation review", "Pre-event project reuse/terms compliance",
                           "Completeness of references and original work", "Scientific validity of agronomic scores", "NASA source eligibility and functioning data retrieval"]}
