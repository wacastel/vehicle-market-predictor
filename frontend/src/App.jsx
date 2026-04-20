import React, { useState } from 'react';

const App = () => {
  const [formData, setFormData] = useState({
    year: 2015,
    mileage: 50000,
    trim: 'C300',
    is_amg: 0,
    is_wagon: 0,
    is_coupe: 0,
    is_cabriolet: 0,
    is_sedan: 1,
    is_manual: 0
  });

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (checked ? 1 : 0) : value
    }));
  };

  const fetchPrediction = async (e) => {
    e.preventDefault();
    setLoading(true);
    setPrediction(null); // Clear previous results
    
    try {
      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ...formData,
            year: parseInt(formData.year),
            mileage: parseInt(formData.mileage)
        }),
      });
      
      const data = await response.json();

      // Catch HTTP 422 and other non-200 responses
      if (!response.ok) {
        // FastAPI returns validation errors inside a "detail" array
        if (data.detail && Array.isArray(data.detail)) {
            // Extract the specific message (e.g., "Input should be less than or equal to 2023")
            throw new Error(`Validation Error: ${data.detail[0].msg}`);
        } else {
            throw new Error(data.message || "An error occurred on the server.");
        }
      }
      
      setPrediction(`$${data.estimated_fair_market_value.toLocaleString()}`);
      
    } catch (error) {
      console.error("Error fetching prediction:", error);
      setPrediction(error.message); // Display the error in the blue box
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '500px', margin: '40px auto', fontFamily: 'sans-serif' }}>
      <h2>C-Class Market Value Predictor</h2>
      
      <form onSubmit={fetchPrediction} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        
        <div>
          <label>Year: </label>
          <input type="number" name="year" value={formData.year} onChange={handleInputChange} required />
        </div>

        <div>
          <label>Mileage: </label>
          <input type="number" name="mileage" value={formData.mileage} onChange={handleInputChange} required />
        </div>

        <div>
          <label>Trim Level: </label>
          <select name="trim" value={formData.trim} onChange={handleInputChange}>
            <option value="C280">C280</option>
            <option value="C300">C300</option>
            <option value="C350">C350</option>
            <option value="C43">C43</option>
            <option value="C63">C63</option>
          </select>
        </div>

        <fieldset>
          <legend>Body Style</legend>
          <label>
            <input type="radio" name="body_style" checked={formData.is_sedan === 1} 
                   onChange={() => setFormData({...formData, is_sedan: 1, is_coupe: 0, is_cabriolet: 0, is_wagon: 0})} /> Sedan
          </label>
          <label>
            <input type="radio" name="body_style" checked={formData.is_coupe === 1} 
                   onChange={() => setFormData({...formData, is_sedan: 0, is_coupe: 1, is_cabriolet: 0, is_wagon: 0})} /> Coupe
          </label>
        </fieldset>

        <div>
          <label>
            <input type="checkbox" name="is_amg" checked={formData.is_amg === 1} onChange={handleInputChange} /> 
            AMG Package
          </label>
        </div>

        <button type="submit" disabled={loading} style={{ padding: '10px', marginTop: '10px' }}>
          {loading ? 'Analyzing Market Data...' : 'Get Valuation'}
        </button>
      </form>

      {prediction !== null && (
        <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#e6f7ff', borderRadius: '8px' }}>
          <h3>Estimated Value: ${typeof prediction === 'number' ? prediction.toLocaleString() : prediction}</h3>
        </div>
      )}
    </div>
  );
};

export default App;
