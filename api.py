from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import pickle
import pandas as pd
import uvicorn

app = FastAPI(title="Vehicle Market Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENSEMBLE ARCHITECTURE ---
# Load both models from our Stage 2 training!
with open("linear_base.pkl", "rb") as f:
    linear_base = pickle.load(f)
    
with open("rf_corrector.pkl", "rb") as f:
    rf_corrector = pickle.load(f)
    
with open("model_columns.pkl", "rb") as f:
    model_columns = pickle.load(f)

# We removed the le=2023 boundary so the model can freely extrapolate new years
class VehicleParams(BaseModel):
    year: int = Field(..., ge=1994, description="Year must be 1994 or newer")
    mileage: int = Field(..., ge=0, le=250000)
    trim: str
    is_amg: int = 0
    is_wagon: int = 0
    is_coupe: int = 0
    is_cabriolet: int = 0
    is_sedan: int = 1
    is_manual: int = 0

    @field_validator('trim')
    @classmethod
    def validate_trim(cls, v: str) -> str:
        allowed_trims = ['C280', 'C300', 'C350', 'C43', 'C63']
        if v not in allowed_trims:
            raise ValueError(f"Trim must be one of {allowed_trims}")
        return v

@app.post("/predict")
def predict_price(vehicle: VehicleParams):
    input_data = vehicle.model_dump() 
    
    df = pd.DataFrame(0, index=[0], columns=model_columns)
    
    df['year'] = input_data['year']
    df['mileage'] = input_data['mileage']
    df['is_amg'] = input_data['is_amg']
    df['is_wagon'] = input_data['is_wagon']
    df['is_coupe'] = input_data['is_coupe']
    df['is_cabriolet'] = input_data['is_cabriolet']
    df['is_sedan'] = input_data['is_sedan']
    df['is_manual'] = input_data['is_manual']
    
    trim_col = f"trim_{input_data['trim']}"
    if trim_col in df.columns:
        df[trim_col] = 1
        
    # --- ENSEMBLE PREDICTION ---
    # 1. Get the baseline linear prediction (which handles the 2025 extrapolation)
    base_price = linear_base.predict(df)[0]
    
    # 2. Get the micro-correction from the Random Forest
    correction = rf_corrector.predict(df)[0]
    
    # 3. Combine them for the final, nuanced valuation
    final_value = base_price + correction
    
    # Floor the value to prevent negative prices on edge-case 300,000-mile cars
    final_value = max(final_value, 1500)
    
    return {
        "status": "success",
        "vehicle_details": input_data,
        "estimated_fair_market_value": round(final_value, 2)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
