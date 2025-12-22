# Manual Testing Scripts

This folder contains scripts for **manual verification** of the data pipeline.

Unlike automated unit tests (which run in the background), these scripts produce visible output files you can read and verify yourself.

## Scripts

### `export_forecast_json.py`

Fetches live data from IMS and exports it to a readable JSON file.

**Usage:**

```bash
python tests/manual/export_forecast_json.py
```

**Output:**

- `output/forecast_YYYY-MM-DD.json` - Full parsed data in readable JSON format

### Example output structure

```json
{
  "_meta": {
    "forecast_date": "2025-12-22",
    "city_count": 15
  },
  "country_forecast": {
    "description_hebrew": "...",
    "description_english": "..."
  },
  "city_forecasts": [
    {
      "city_name_english": "Jerusalem",
      "temperature": {"min": 8, "max": 19},
      "weather": {"description_hebrew": "בהיר"}
    }
  ]
}
```

## Output Folder

The `output/` subfolder stores generated files. It's gitignored so you won't accidentally commit test data.
