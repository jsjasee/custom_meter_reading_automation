---
title: Meter Reading Report
emoji: "📧"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.19.0
python_version: 3.12
app_file: app.py
suggested_hardware: cpu-basic
short_description: Upload .eml meter emails, preview the HTML report, and send it by SMTP.
---

# Meter Reading Report

Upload one or more `.eml` files, click **Process**, preview the generated HTML table, and send the report email via SMTP.

## Hugging Face Space setup

1. Create a new Space and choose the `Gradio` SDK.
2. Push this repository to the Space.
3. In the Space `Settings` page, add these as `Secrets`:
   - `SMTP_FROM`
   - `SMTP_PASSWORD`
   - `SMTP_TO`
4. The app reads those values from environment variables at runtime.

## Notes

- Keep `.env` local only. Do not upload it to the Space.
- The Space accepts multiple `.eml` files in one run.
