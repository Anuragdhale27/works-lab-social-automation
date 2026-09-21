# Works Lab Social Automation — Starter

This starter uses the five approved Works Lab resume designs as the creative base.

## Current flow

1. Pick a rotating hook from `data/hooks.json`.
2. Pick one of the five resume designs.
3. Generate a 1080×1080 Instagram creative with Pillow.
4. Save the result under `generated_ads/`.
5. Later, connect the Meta Instagram publishing API and WhatsApp Cloud API using GitHub Actions secrets.

## Important

- No Instagram/WhatsApp secrets are included in this repository.
- The image generator itself is local/free; it does not require an AI image API.
- For Instagram API publishing, the generated image must be reachable from a public URL.
- The recommended next step is to put the repository on GitHub and enable GitHub Pages (or use your existing static site) for `generated_ads/`.

## Planned secrets

`IG_ACCESS_TOKEN`
`IG_USER_ID`
`WA_ACCESS_TOKEN`
`WA_PHONE_NUMBER_ID`
`WA_RECIPIENT`
`WA_TEMPLATE_NAME` (when required by the WhatsApp messaging flow)

These values belong in GitHub repository Secrets, not in source files.

## Run locally

```bash
pip install -r requirements.txt
python scripts/generate_ad.py
```

GitHub Actions can schedule this daily. Scheduled workflows run on the default branch; GitHub notes that scheduled runs can be delayed under high load, so avoid scheduling exactly at the top of the hour.
