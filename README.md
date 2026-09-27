# Works Lab Social Automation

This repository generates and publishes daily Works Lab Instagram creatives.

## Products

### Resume
- Website: https://resume.workslab.in
- Existing workflow: `.github/workflows/daily-creative.yml`
- Existing resume automation is unchanged by the Tracker feature.

### Tracker
- Website: https://tracker.workslab.in
- Workflow: `.github/workflows/daily-tracker.yml`
- Runs daily at **7:07 PM IST**.
- Generates a new Tracker creative using the Tracker website visual system.
- Publishes it to the same Instagram account using the existing `IG_ACCESS_TOKEN` and `IG_USER_ID` secrets.
- Uses the existing WhatsApp secrets when configured; WhatsApp failure does not block Instagram publishing.

## Tracker creative system

Tracker creatives match the product UI:
- cream paper-like background
- subtle dotted grid
- dark chocolate brown typography
- Works Lab orange accent
- thin brown borders
- editorial serif headlines
- clean sans-serif body copy
- financial dashboard / tracker cards
- Indian rupee amounts and categories

The Tracker content engine rotates through hooks covering salary, budgeting, EMI, UPI spending, savings, wedding planning, trip planning, goals, privacy, features and product demonstrations.

## Tracker content format

Every post contains:
1. Hook
2. Body/problem explanation
3. Value points
4. CTA
5. Tracker website URL

Content is stored in `data/tracker_hooks.json`.

## Run locally

```bash
pip install -r requirements.txt
python scripts/generate_tracker_ad.py
```

Generated files:
- `generated_ads/tracker-daily-YYYY-MM-DD.jpg`
- `generated_ads/tracker-daily-YYYY-MM-DD.json`

No Instagram or WhatsApp secrets are stored in source code.
