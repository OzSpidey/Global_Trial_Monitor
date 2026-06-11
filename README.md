# Clinical Trial Intelligence Dashboard

**Live Demo:** https://global-trial-monitor.onrender.com

> Real-time intelligence across 1,500+ clinical trials, live data from ClinicalTrials.gov API v2, spanning 8 disease areas, with phase pipeline tracking, sponsor leaderboards, geographic distribution, and NLP-driven trending conditions.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Plotly%20Dash-4.x-00B4D8?style=flat&logo=plotly&logoColor=white)
![ClinicalTrials](https://img.shields.io/badge/Data-ClinicalTrials.gov-7c3aed?style=flat)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Screenshots

| Pipeline Overview | Disease Intelligence |
|:-----------------:|:--------------------:|
| ![Pipeline Overview](screenshots/01_pipeline_overview.png) | ![Disease Intelligence](screenshots/02_disease_intelligence.png) |

| Sponsor Leaderboard | Geographic Distribution |
|:-------------------:|:-----------------------:|
| ![Sponsor Leaderboard](screenshots/03_sponsor_leaderboard.png) | ![Geographic Distribution](screenshots/04_geographic.png) |

| Trial Tracker | |
|:-------------:|-|
| ![Trial Tracker](screenshots/05_trial_tracker.png) | |

---

## Features

### ðŸ“Š Pipeline Overview
Four KPI tiles, Total Trials, Actively Recruiting, Avg Trial Duration, Countries Covered, plus a phase distribution bar chart (Early Phase 1 through Phase 4), status breakdown donut, and top-10 sponsor bar chart.

### ðŸ§¬ Disease Intelligence
Treemap breaking down disease areas into specific conditions by study count, top-15 trending conditions bar chart extracted by NLP keyword frequency from trial titles, and a disease area Ã— phase stacked bar showing which phases dominate each therapeutic area.

### ðŸ† Sponsor Leaderboard
Top 20 sponsors ranked by active trial count with dominant phase coloring, sponsor phase breakdown cross-chart (top 10 sponsors Ã— phase), and KPIs for total sponsors, average trials per sponsor, and most active sponsor.

### ðŸŒ Geographic Distribution
Plotly choropleth world map colored by trial density per country, top-15 countries horizontal bar, and a country Ã— status stacked bar, revealing where trials are running and what stage they're in by region.

### ðŸ” Trial Tracker
Fully searchable and filterable table, filter by keyword, status, disease area, and phase simultaneously. Each row shows NCT ID (linked to clinicaltrials.gov), title, phase badge, status badge with color coding, sponsor, countries, and start date. Paginated at 25 rows per page.

---

## Data Coverage

| Disease Area | Query |
|---|---|
| Oncology | cancer, tumor, oncology |
| Cardiovascular | heart disease, cardiovascular, hypertension |
| Neurology | alzheimer, parkinson, multiple sclerosis, stroke |
| Infectious Diseases | HIV, tuberculosis, hepatitis, malaria |
| Diabetes | diabetes, insulin, glycemic |
| Mental Health | depression, anxiety, schizophrenia, bipolar |
| Respiratory | asthma, COPD, pulmonary fibrosis |
| Rare Diseases | rare disease, orphan disease |

Up to **200 trials fetched per disease area** (1,600 total), auto-refreshed every hour via APScheduler.

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Plotly Dash 4.x + Dash Bootstrap Components |
| Charts | Plotly 6.x, choropleth, treemap, bar, donut, scatter |
| Data | ClinicalTrials.gov REST API v2 (no auth required) |
| NLP | Keyword frequency extraction with custom stopword list |
| Storage | SQLite, JSON-serialised list columns, 1-table design |
| Scheduler | APScheduler `BackgroundScheduler`, 1-hour refresh |

---

## Quick Start

```bash
git clone https://github.com/OzSpidey/clinical-trial-dashboard.git
cd clinical-trial-dashboard

pip install -r requirements.txt
python dashboard.py
# Open http://localhost:8051
```

The first run fetches ~1,600 trials from ClinicalTrials.gov in the background (takes 1â€“2 minutes). The UI renders immediately with "Fetching dataâ€¦" placeholders and populates as each disease area completes.

---

## Project Structure

```
clinical-trial-dashboard/
â”œâ”€â”€ dashboard.py        # Plotly Dash app, 5 tabs, 7 callbacks
â”œâ”€â”€ config.py           # Disease areas, status/phase colors, DB path
â”œâ”€â”€ fetcher.py          # ClinicalTrials.gov API v2, pagination + extraction
â”œâ”€â”€ store.py            # SQLite layer, upsert, queries, stats
â”œâ”€â”€ scheduler.py        # APScheduler hourly background refresh
â”œâ”€â”€ nlp.py              # Keyword extraction for trending conditions
â”œâ”€â”€ assets/
â”‚   â””â”€â”€ dashboard.css   # Dark glassmorphism theme
â”œâ”€â”€ data/               # Auto-created; holds trials.db (gitignored)
â””â”€â”€ requirements.txt
```

---

## Data Flow

```
Every hour (APScheduler)
    â”‚
    â”œâ”€â–º fetcher.fetch_all_disease_areas()
    â”‚       â””â”€â”€ 8 disease queries Ã— up to 200 results each
    â”‚           pagination via nextPageToken loop
    â”œâ”€â–º store.upsert_trials()
    â”‚       â””â”€â”€ INSERT OR REPLACE into SQLite
    â””â”€â–º scheduler._last_run updated

Dashboard callbacks (on interval tick or user interaction)
    â”‚
    â”œâ”€â–º store.get_trials()       â†’ all tabs (cached DataFrame)
    â”œâ”€â–º store.get_stats()        â†’ KPI tiles
    â”œâ”€â–º nlp.get_trending_conditions()  â†’ Disease Intelligence tab
    â””â”€â–º Plotly figures computed in-process from SQLite data
```

---

## API Reference

ClinicalTrials.gov v2 endpoint used:
```
GET https://clinicaltrials.gov/api/v2/studies
    ?query.cond=<condition>
    &filter.status=<status>
    &pageSize=100
    &pageToken=<token>   # for pagination
    &format=json
```
No API key, no rate limit documented, polite 0.2s delay between pages.

---

## Requirements

```
dash>=2.14.0
dash-bootstrap-components>=1.4.0
plotly>=5.17.0
pandas>=2.0.0
numpy>=1.24.0,<2.0
requests>=2.31.0
apscheduler>=3.10.1
```

---

## Related Projects

- [Stock Sentiment Dashboard](https://github.com/OzSpidey/stock-sentiment-dashboard), Real-time NLP sentiment for 15 stocks
- [IPL Analytics Dashboard](https://github.com/OzSpidey/ipl-analytics-dashboard), 19 seasons of IPL cricket statistics
- [Customer Churn Intelligence Platform](https://github.com/OzSpidey/churn-predictor-dashboard), XGBoost + SHAP churn prediction

---

*Built with Plotly Dash Â· ClinicalTrials.gov API Â· APScheduler*

