# YTMusicAPI

## Local

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Vercel

This project is configured for Vercel with:

- `api/index.py` as the serverless entrypoint
- `vercel.json` routing all requests to the FastAPI app

For better serverless reliability, `/search` no longer fetches lyrics for every song result.
Use `/lyrics?videoId=...` to request lyrics for a specific song.
