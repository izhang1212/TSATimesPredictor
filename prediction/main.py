"""
main.py - orchestrates the full TSA wait time prediction pipeline

Steps:
    1. Generate seed data (if needed)
    2. Load normalized CSVs into tsa.db
    3. Export training data from the DB
    4. Build engineered features
    5. Train LightGBM
    6. Train Prophet (one model per airport)
    7. Run a sample prediction through the ensemble
"""

from db.seed_data import generate as generate_seed_data
from db.build_db import build_all, get_db, export_training_data, get_summary
from db.build_features import build_features
from models.lightgbm_model import run_training_pipeline as train_lightgbm
from models.prophet_model import run_training_pipeline as train_prophet
from models.ensemble import predict_wait_time


def main():
    # --- Step 1: seed data -------------------------------------------------
    print("=" * 60)
    print("STEP 1: Generating seed data")
    print("=" * 60)
    seed_summary = generate_seed_data()
    print(f"Seed data written for {seed_summary['airports']} airports, "
          f"{seed_summary['days']} days")
    print(f"  wait_times rows:  {seed_summary['wait_times_rows']:,}")
    print(f"  throughput rows:  {seed_summary['throughput_rows']:,}")
    print(f"  flights rows:     {seed_summary['flights_rows']:,}")
    print(f"  weather rows:     {seed_summary['weather_rows']:,}")

    # --- Step 2: load into DB ---------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 2: Loading normalized data into tsa.db")
    print("=" * 60)
    db_summary = build_all()
    print("Rows loaded per table:")
    for table, count in db_summary.items():
        print(f"  {table:<15} {count:,}")

    # --- Step 3: export training data -------------------------------------
    print("\n" + "=" * 60)
    print("STEP 3: Exporting joined training data")
    print("=" * 60)
    conn = get_db()
    n_exported = export_training_data(conn)
    summary = get_summary(conn)
    conn.close()
    print(f"Exported {n_exported:,} rows to data/exports/training_data.csv")
    print(f"DB totals: {summary}")

    # --- Step 4: build engineered features --------------------------------
    print("\n" + "=" * 60)
    print("STEP 4: Building engineered features")
    print("=" * 60)
    n_features = build_features()
    print(f"Wrote {n_features:,} rows to data/exports/training_data_final.csv")

    # --- Step 5: train LightGBM -------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 5: Training LightGBM")
    print("=" * 60)
    lgb_results = train_lightgbm()
    m = lgb_results["metrics"]
    print(f"  Training samples: {lgb_results['train_size']:,}")
    print(f"  Test samples:     {lgb_results['test_size']:,}")
    print(f"  MAE:              {m['mae']:.2f} minutes")
    print(f"  RMSE:             {m['rmse']:.2f} minutes")
    print(f"  Within 5 min:     {m['within_5_min']:.1%}")
    print(f"  Within 10 min:    {m['within_10_min']:.1%}")
    print(f"  Best iteration:   {m['best_iteration']}")
    print("  Top 5 features by importance:")
    for feat, imp in lgb_results["feature_importance"][:5]:
        print(f"    {feat:<40} {imp:>10.0f}")

    # --- Step 6: train Prophet --------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 6: Training Prophet (one model per airport)")
    print("=" * 60)
    prophet_results = train_prophet()
    overall = prophet_results["overall_metrics"]
    print(f"  Airports trained: {overall.get('n_airports_trained', 0)}")
    print(f"  Airports skipped: {overall.get('n_airports_skipped', 0)}")
    print(f"  Average MAE:      {overall.get('mae', 0):.2f} minutes")
    print(f"  Average RMSE:     {overall.get('rmse', 0):.2f} minutes")
    print(f"  Within 10 min:    {overall.get('within_10_min', 0):.1%}")

    # --- Step 7: sample prediction ----------------------------------------
    print("\n" + "=" * 60)
    print("STEP 7: Sample prediction via ensemble")
    print("=" * 60)
    test_cases = [
        ("JFK", "2026-02-15", 7),   # Monday morning rush
        ("JFK", "2026-02-15", 14),  # Midday
        ("LGA", "2026-02-21", 17),  # Sunday evening
        ("LAX", "2026-07-04", 10),  # Holiday
        ("JFK", "2026-04-23", 14),  # today
    ]
    for airport, date_str, hour in test_cases:
        result = predict_wait_time(airport, date_str, hour)
        print(f"\n  {airport} on {date_str} at {hour:02d}:00")
        print(f"    Prediction: {result['prediction_minutes']} min ({result['tier']})")
        print(f"    Range:      {result['range_low']} - {result['range_high']} min")
        print(f"    LightGBM:   {result['model_predictions']['lightgbm']} min")
        print(f"    Prophet:    {result['model_predictions']['prophet']} min")
        print(f"    Weights:    LGB={result['weights']['lightgbm']:.2f}, "
              f"Prophet={result['weights']['prophet']:.2f}")

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()