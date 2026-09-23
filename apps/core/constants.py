DEFAULT_FINDING_CATEGORIES = [
    "Documentation",
    "Hardware",
    "Software",
    "Visual System",
    "Motion System",
    "Instructor Station",
    "Sound System",
    "Other",
]

STANDARD_FOLDERS = [
    {"name": "Manuals", "icon": "📘"},
    {"name": "QTG", "icon": "📈"},
    {"name": "Subjective Tests", "icon": "✍️"},
    {"name": "MQTG", "icon": "📕"},
    {"name": "Maintenance", "icon": "🛠️"},
    {"name": "Authority Documentation", "icon": "🏛️"},
    {"name": "Closure Evidence", "icon": "🔒"},
]

FOLDER_ICON_CHOICES = [
    "📁",
    "📘",
    "📗",
    "📕",
    "📈",
    "✍️",
    "🛠️",
    "🏛️",
    "🔒",
    "🗂️",
    "📄",
    "✈️",
    "🎯",
    "🧾",
    "📦",
]

MAINTENANCE_PROGRAMS = {
    "program_a": [
        {"key": "monthly", "name": "Monthly Inspection", "kind": "monthly"},
        {"key": "annual", "name": "12-Month Inspection", "kind": "annual"},
        {
            "key": "hours300",
            "name": "300-Hour Inspection",
            "kind": "hours",
            "hours_interval": 300,
        },
        {"key": "3_year", "name": "3-Year Inspection", "kind": "3_year"},
        {"key": "as_required", "name": "As Required", "kind": "as_required"},
    ],
    "program_b": [
        {"key": "monthly", "name": "Monthly Inspection", "kind": "monthly"},
        {
            "key": "hours300",
            "name": "300-Hour Inspection",
            "kind": "hours",
            "hours_interval": 300,
        },
        {"key": "6_month", "name": "6-Month Inspection", "kind": "6_month"},
        {"key": "annual", "name": "12-Month Inspection", "kind": "annual"},
        {"key": "as_required", "name": "As Required", "kind": "as_required"},
    ],
    "program_c": [
        {"key": "q1", "name": "Q1 Inspection", "kind": "quarterly_fixed"},
        {"key": "q2", "name": "Q2 Inspection", "kind": "quarterly_fixed"},
        {"key": "q3", "name": "Q3 Inspection", "kind": "quarterly_fixed"},
        {"key": "q4", "name": "Q4 Inspection", "kind": "quarterly_fixed"},
        {"key": "sem1", "name": "Semester 1 Inspection", "kind": "semester_fixed"},
        {"key": "sem2", "name": "Semester 2 Inspection", "kind": "semester_fixed"},
        {"key": "annual", "name": "12-Month Inspection", "kind": "annual"},
    ],
}

HIL_CATEGORIES = {
    "MIN": {"label": "Minor (MIN)", "days": 90},
    "MAJ": {"label": "Major (MAJ)", "days": 30},
    "OBS": {"label": "Observation (OBS)", "days": None},
}
