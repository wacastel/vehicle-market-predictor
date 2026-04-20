# Vehicle Market Predictor

An end-to-end Machine Learning application that predicts the fair market value of high-performance vehicles (specifically Mercedes-Benz C-Class) based on real-world auction data.

## The Machine Learning Architecture

This project uses a **Residual Ensemble** architecture, combining the strengths of two different machine learning algorithms to overcome their individual weaknesses.

### 1. Linear Regression (The Extrapolator)
Linear Regression models the relationship between variables by fitting a linear equation to the data. 
* **The Strength:** It understands global trends and can **extrapolate**. If it learns a car loses $2,000 in value every year, it can mathematically apply that rule to a brand new 2025 or 2026 model, even if the training data only went up to 2023.
* **The Weakness:** It struggles with non-linear nuances. It can't easily understand that an AMG package might add $10,000 to a 2018 model but only $3,000 to a 2005 model.

### 2. Random Forest (The Interpolator)
A Random Forest is an ensemble of Decision Trees. It splits data into highly specific "buckets" (leaf nodes) based on feature thresholds.
* **The Strength:** It is incredible at capturing non-linear, complex interactions (e.g., the specific premium of a manual transmission on a C63 trim). 
* **The Weakness:** It **cannot extrapolate**. If asked to predict the price of a 2025 model, it simply drops it into the "2023 and newer" bucket and spits out the average price of its older training data, resulting in massive underpricing for new cars.

### 3. The Residual Ensemble (The Solution)
To get the best of both worlds, this application uses a two-stage process:
1.  **The Base:** The Linear Regression model calculates a baseline price, successfully handling the mathematical depreciation curve for any year or mileage.
2.  **The Correction:** The Random Forest is trained *only on the errors (residuals)* of the Linear model. It learns the specific premiums and discounts associated with trims and packages that the linear model missed.
3.  **The Final Prediction:** `Base Price (Linear) + Micro-Correction (Random Forest)`

---

## Setup & Deployment

### Phase 1: The FastAPI Backend
The backend serves the trained ML models and validates incoming data.

1. **Navigate to the project root:**
   cd vehicle-market-predictor
   
2. **Activate the virtual environment:**
   source .venv/bin/activate
   
3. **Install dependencies:**
   pip install fastapi uvicorn pydantic pandas scikit-learn
   
4. **Run the server:**
   python api.py
   
   (The API will start on http://localhost:8000)

### Phase 2: The React/Vite Frontend
The frontend provides a clean user interface to query the model.

1. **Open a new terminal window** and navigate to the frontend directory:
   cd vehicle-market-predictor/frontend
   
2. **Install Node dependencies:**
   (Note: If using an Apple Silicon Mac, use the --force flag to resolve optional esbuild binaries)
   npm install --force
   
3. **Start the development server:**
   npm run dev
   
   (The UI will be available at http://localhost:5173)