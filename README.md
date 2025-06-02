# OpenMRS-OpenIMIS Integration Middleware

A prototype middleware system that facilitates data exchange between OpenMRS (an open-source medical record system) and OpenIMIS (an open-source health insurance claims system) using FHIR standards. This system is built using FastAPI for the backend and Streamlit for the frontend interface.

## Features

- 🧑‍⚕️ **Patient Registration**: Register new patients with basic information
- 📝 **Medical Encounters**: Record patient visits, diagnoses, and treatments
- 💰 **FHIR Claims**: Generate and submit insurance claims in FHIR format
- 📊 **Monthly Reporting**: View consolidated statistics and detailed reports
- ⚙️ **Administration**: System management and data reset capabilities

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```powershell
git clone <repository-url>
cd openmrs_openimis
```

2. Create and activate a virtual environment (optional but recommended):
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

3. Install the required dependencies:
```powershell
pip install -r requirements.txt
```

## Running the Application

The application consists of two components that need to be run separately:

1. Start the FastAPI backend server:
```powershell
uvicorn main:app --reload
```
The backend will be available at http://localhost:8000

2. In a new terminal, start the Streamlit frontend:
```powershell
streamlit run app.py
```
The frontend will automatically open in your default web browser at http://localhost:8501

## Usage

1. **Patient Registration**
   - Navigate to "Register Patient" in the sidebar
   - Fill in patient details (name, age, gender, chief complaint)
   - Submit to create a new patient record

2. **Recording Encounters**
   - Go to "Record Encounter"
   - Select an existing patient
   - Enter visit details, diagnosis, and treatment
   - Save the encounter

3. **Submitting Claims**
   - Access "Submit Claim"
   - Search and select an encounter
   - Review the generated FHIR claim
   - Submit the claim

4. **Viewing Reports**
   - Open "Monthly Report"
   - Select a month to view statistics
   - Use filters to analyze specific data
   - Export or review detailed tables

5. **Administration**
   - Access system statistics
   - Reset data if needed (requires confirmation)

## API Documentation

The FastAPI backend provides automatic API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
openmrs_openimis/
├── main.py           # FastAPI backend server
├── app.py           # Streamlit frontend application
└── requirements.txt  # Python dependencies
```

## Technical Details

- Backend: FastAPI with in-memory storage
- Frontend: Streamlit with interactive components
- Data Format: FHIR-compliant JSON for claims
- Authentication: Not implemented in prototype

## Limitations

- Uses in-memory storage (data is lost when server restarts)
- Basic FHIR compliance for demonstration
- No real connection to OpenMRS or OpenIMIS
- Limited security features

## Development

To modify or extend the application:

1. Backend changes:
   - Edit `main.py` to add/modify API endpoints
   - Use Pydantic models for data validation
   - Restart the uvicorn server to apply changes

2. Frontend changes:
   - Modify `app.py` to update the UI
   - Changes are automatically reloaded by Streamlit

## Troubleshooting

1. If you can't connect to the backend:
   - Ensure the FastAPI server is running
   - Check if port 8000 is available

2. If the frontend doesn't load:
   - Verify Streamlit installation
   - Check if port 8501 is free
   - Clear browser cache if needed

3. If data isn't persisting:
   - Remember this is an in-memory system
   - Data resets when the backend server restarts
