# REACH — AI-Powered Market Development Platform

REACH is a market-development product that turns a product or service description into a structured workflow for market strategy, organisation discovery, decision-maker research, enrichment and opportunity management.

## Portfolio demo

This repository is the **safe portfolio/demo build** of REACH.

- Uses fictional/sample demonstration data
- Makes **no OpenAI API calls**
- Makes **no Hunter API calls**
- Makes **no Companies House API calls**
- Makes **no Supabase database/authentication calls during the demo journey**
- Contains **no API keys or `.env` secrets**
- Does not send emails, make calls, or contact real organisations

The production/development version is kept separately and connects to approved external services.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Safety

Never commit `.env` or `.streamlit/secrets.toml`. They are excluded by `.gitignore`.

## Status

Active development. This public build is designed to demonstrate the REACH product experience without consuming external API credits.
