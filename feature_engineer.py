import pandas as pd
import re
import numpy as np

INPUT_CSV = "bat_c_class_historical_data.csv"
OUTPUT_CSV = "c_class_ml_features.csv"

def parse_mileage(title):
    """
    Extracts mileage from BaT titles. Handles '45k-Mile', '2,700-Mile', etc.
    Returns the integer value, or NaN if not listed.
    """
    # Look for patterns like "45k-Mile" or "2,700-Mile"
    match = re.search(r'([\d,]+)(k?)-[Mm]ile', title)
    if match:
        val = match.group(1).replace(',', '')
        multiplier = 1000 if match.group(2) == 'k' else 1
        return int(val) * multiplier
    return np.nan

def extract_features(df):
    print("Starting feature extraction...")

    # 1. Extract the Year
    # Looks for a 4-digit number starting with 19 or 20
    df['year'] = df['raw_title'].str.extract(r'\b(19\d{2}|20\d{2})\b').astype(float)

    # 2. Extract Mileage using our custom function
    df['mileage'] = df['raw_title'].apply(parse_mileage)

    # 3. Extract Trim Level (The "Secret Sauce" for pricing)
    # This regex looks for 'C' followed by 2 or 3 digits (e.g., C300, C63, C43)
    df['trim'] = df['raw_title'].str.extract(r'(C\d{2,3})')
    
    # 4. Flag AMG Models (High impact on target variable)
    df['is_amg'] = df['raw_title'].str.contains(r'\bAMG\b', case=False).astype(int)

    # 5. Extract Body Style
    df['is_wagon'] = df['raw_title'].str.contains(r'\bWagon|Estate\b', case=False).astype(int)
    df['is_coupe'] = df['raw_title'].str.contains(r'\bCoupe\b', case=False).astype(int)
    df['is_cabriolet'] = df['raw_title'].str.contains(r'\bCabriolet|Convertible\b', case=False).astype(int)
    # If it's not a wagon, coupe, or cabriolet, it's highly likely a sedan
    df['is_sedan'] = ((df['is_wagon'] == 0) & (df['is_coupe'] == 0) & (df['is_cabriolet'] == 0)).astype(int)

    # 6. Flag Manual Transmissions (Rare in C-Class, carries a massive premium)
    df['is_manual'] = df['raw_title'].str.contains(r'\b5-Speed|6-Speed\b', case=False).astype(int)

    # Clean up the price column (ensure it is a strict integer)
    df['price'] = df['raw_price'].astype(int)

    # Drop the raw columns that the ML model can't use
    ml_df = df.drop(columns=['raw_title', 'raw_price', 'is_sold', 'auction_url'])

    return ml_df

def main():
    print(f"Loading {INPUT_CSV}...")
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"[!] Could not find {INPUT_CSV}. Ensure it is in the same directory.")
        return

    ml_df = extract_features(df)

    # Handle Missing Values (Imputation)
    # If mileage is missing, we'll impute it with the median mileage of that specific Year and Trim
    # This is a classic ML technique to save rows with missing data.
    print("Handling missing mileage data via median imputation...")
    ml_df['mileage'] = ml_df.groupby(['year', 'trim'])['mileage'].transform(
        lambda x: x.fillna(x.median())
    )
    # If there are still NaNs (e.g., a unique trim/year combo with no other cars to pull a median from), 
    # fill with the global median.
    ml_df['mileage'] = ml_df['mileage'].fillna(ml_df['mileage'].median())

    # Final cleanup: drop rows where we couldn't even find a year or trim
    ml_df = ml_df.dropna(subset=['year', 'trim'])

    print(f"\nFinal ML Dataset Shape: {ml_df.shape[0]} rows, {ml_df.shape[1]} features.")
    
    # Save the polished artifact
    ml_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Machine Learning ready data saved to {OUTPUT_CSV}")
    print("\nSample Data:")
    print(ml_df.head())

if __name__ == "__main__":
    main()
