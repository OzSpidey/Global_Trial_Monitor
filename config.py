"""Central configuration for Clinical Trial Intelligence Dashboard."""

DB_PATH            = "data/trials.db"
REFRESH_INTERVAL_S = 3600   # refresh every hour
MAX_PER_DISEASE    = 200    # studies per disease area to fetch

# Color palette
BG      = "#0a0a1a"
CARD_BG = "rgba(18,18,42,0.95)"
BORDER  = "rgba(255,255,255,0.08)"
TEXT    = "#e2e2f0"
MUTED   = "#6b7280"
ACCENT  = "#7c3aed"
GREEN   = "#22c55e"
RED     = "#ef4444"
YELLOW  = "#f59e0b"
BLUE    = "#3b82f6"
ORANGE  = "#f97316"

# Disease areas with ClinicalTrials.gov search queries
DISEASE_AREAS = {
    "Oncology":       "cancer OR tumor OR oncology",
    "Cardiovascular": "heart disease OR cardiovascular OR hypertension",
    "Neurology":      "alzheimer OR parkinson OR multiple sclerosis OR stroke",
    "Infectious":     "HIV OR tuberculosis OR hepatitis OR malaria",
    "Diabetes":       "diabetes OR insulin OR glycemic",
    "Mental Health":  "depression OR anxiety OR schizophrenia OR bipolar",
    "Respiratory":    "asthma OR COPD OR pulmonary fibrosis",
    "Rare Diseases":  "rare disease OR orphan disease",
}

# Status display colors
STATUS_COLORS = {
    "RECRUITING":            "#22c55e",
    "ACTIVE_NOT_RECRUITING": "#3b82f6",
    "COMPLETED":             "#6b7280",
    "NOT_YET_RECRUITING":    "#f59e0b",
    "TERMINATED":            "#ef4444",
    "WITHDRAWN":             "#f97316",
    "SUSPENDED":             "#a855f7",
    "UNKNOWN":               "#374151",
}

# Phase ordering and display labels
PHASE_ORDER  = ["EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4", "NA"]
PHASE_LABELS = {
    "EARLY_PHASE1": "Early Ph.1",
    "PHASE1":       "Phase 1",
    "PHASE2":       "Phase 2",
    "PHASE3":       "Phase 3",
    "PHASE4":       "Phase 4",
    "NA":           "N/A",
}
PHASE_COLORS = {
    "EARLY_PHASE1": "#a855f7",
    "PHASE1":       "#3b82f6",
    "PHASE2":       "#22c55e",
    "PHASE3":       "#f59e0b",
    "PHASE4":       "#ef4444",
    "NA":           "#6b7280",
}
