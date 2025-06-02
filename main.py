from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

app = FastAPI(
    title="OpenMRS-OpenIMIS Integration API",
    description="A prototype middleware for healthcare data integration",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for patients
patients = {}
# In-memory storage for encounters
encounters = {}
# In-memory storage for claims
claims = {}

class Patient(BaseModel):
    full_name: str
    age: int
    gender: str
    chief_complaint: str
    patient_id: Optional[str] = None
    created_at: Optional[str] = None

class Encounter(BaseModel):
    patient_id: str
    diagnosis: str
    treatment: str
    visit_date: Optional[str] = None
    attending_clinician: Optional[str] = None
    encounter_id: Optional[str] = None
    created_at: Optional[str] = None

class ClaimCoding(BaseModel):
    system: Optional[str] = None
    code: str

class ClaimType(BaseModel):
    coding: List[ClaimCoding]

class Reference(BaseModel):
    reference: str

class Money(BaseModel):
    value: float
    currency: str = "USD"

class ClaimItem(BaseModel):
    sequence: int
    productOrService: Dict[str, List[ClaimCoding]]
    servicedDate: str
    unitPrice: Money
    net: Money

class FHIRClaim(BaseModel):
    resourceType: str = "Claim"
    id: Optional[str] = None
    status: str = "active"
    type: ClaimType
    patient: Reference
    encounter: Reference
    created: str
    provider: Optional[Reference] = None
    use: str = "claim"
    priority: Dict[str, List[Dict[str, str]]] = Field(
        default={"coding": [{"code": "normal"}]}
    )
    item: List[ClaimItem]
    total: Money

    @validator('resourceType')
    def validate_resource_type(cls, v):
        if v != "Claim":
            raise ValueError('resourceType must be "Claim"')
        return v

def map_encounter_to_claim(encounter_id: str) -> dict:
    # Find the encounter and associated patient
    for patient_id, patient_encounters in encounters.items():
        for enc in patient_encounters:
            if enc.encounter_id == encounter_id:
                # Generate a simple treatment code based on diagnosis
                treatment_code = f"TREAT{abs(hash(enc.diagnosis)) % 1000:03d}"
                
                # Calculate a dummy charge (based on diagnosis length as an example)
                base_amount = 100.0
                complexity_factor = len(enc.diagnosis) / 20  # Longer diagnosis = higher charge
                total_amount = round(base_amount * (1 + complexity_factor), 2)

                # Construct the FHIR Claim
                claim = {
                    "resourceType": "Claim",
                    "status": "active",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                                "code": "institutional"
                            }
                        ]
                    },
                    "patient": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc.encounter_id}"},
                    "created": datetime.now().isoformat(),
                    "use": "claim",
                    "priority": {"coding": [{"code": "normal"}]},
                    "item": [
                        {
                            "sequence": 1,
                            "productOrService": {
                                "coding": [
                                    {
                                        "code": treatment_code,
                                        "system": "http://example.org/local-codes"
                                    }
                                ]
                            },
                            "servicedDate": enc.visit_date,
                            "unitPrice": {"value": total_amount, "currency": "USD"},
                            "net": {"value": total_amount, "currency": "USD"}
                        }
                    ],
                    "total": {"value": total_amount, "currency": "USD"}
                }

                if enc.attending_clinician:
                    claim["provider"] = {
                        "reference": f"Practitioner/{abs(hash(enc.attending_clinician)) % 10000:04d}"
                    }

                return claim
                
    raise HTTPException(status_code=404, detail="Encounter not found")

def filter_by_month(date_str: str, target_month: str) -> bool:
    """Helper function to check if a date falls within a specific month"""
    try:
        return date_str.startswith(target_month)
    except:
        return False

@app.post("/patient", status_code=201)
async def create_patient(patient: Patient):
    # Generate a unique patient ID
    patient.patient_id = str(uuid.uuid4())
    patient.created_at = datetime.now().isoformat()
    
    # Store patient in our in-memory storage
    patients[patient.patient_id] = patient
    
    # Return the complete patient record
    return {
        "status": "success",
        "message": "Patient created successfully",
        "data": patient.dict()
    }

@app.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    if patient_id not in patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patients[patient_id]

@app.post("/encounter", status_code=201)
async def create_encounter(encounter: Encounter):
    # Validate that patient exists
    if encounter.patient_id not in patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Generate unique encounter ID and set timestamps
    encounter.encounter_id = str(uuid.uuid4())
    encounter.created_at = datetime.now().isoformat()
    if not encounter.visit_date:
        encounter.visit_date = datetime.now().date().isoformat()
    
    # Initialize encounters list for patient if it doesn't exist
    if encounter.patient_id not in encounters:
        encounters[encounter.patient_id] = []
    
    # Store encounter
    encounters[encounter.patient_id].append(encounter)
    
    # Return the complete encounter record
    return {
        "status": "success",
        "message": "Encounter recorded successfully",
        "data": encounter.dict()
    }

@app.get("/encounter/{patient_id}")
async def get_patient_encounters(patient_id: str):
    if patient_id not in patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient_id not in encounters:
        return []
    return encounters[patient_id]

@app.get("/patients")
async def get_all_patients():
    return list(patients.values())

@app.get("/encounters")
async def list_encounters():
    """Return a list of all encounters with basic metadata"""
    result = []
    for patient_id, patient_encounters in encounters.items():
        patient = patients[patient_id]
        for enc in patient_encounters:
            result.append({
                "encounter_id": enc.encounter_id,
                "patient_name": patient.full_name,
                "visit_date": enc.visit_date,
                "diagnosis": enc.diagnosis[:50] + "..." if len(enc.diagnosis) > 50 else enc.diagnosis
            })
    return result

@app.get("/encounters/{encounter_id}")
async def get_encounter(encounter_id: str):
    """Return full encounter data for a specific encounter"""
    for patient_encounters in encounters.values():
        for enc in patient_encounters:
            if enc.encounter_id == encounter_id:
                return enc
    raise HTTPException(status_code=404, detail="Encounter not found")

@app.post("/claim", status_code=201)
async def submit_claim(claim: FHIRClaim):
    """Submit a FHIR Claim and get a response"""
    claim_id = str(uuid.uuid4())
    claim.id = claim_id
    claims[claim_id] = claim

    return JSONResponse(
        status_code=201,
        content={
            "claim_id": claim_id,
            "status": "accepted",
            "received": datetime.now().isoformat()
        }
    )

@app.get("/claims")
async def list_claims():
    """Return all stored claims (for verification)"""
    return list(claims.values())

@app.get("/encounters/{encounter_id}/claim")
async def generate_claim_preview(encounter_id: str):
    """Generate a FHIR Claim preview for a specific encounter"""
    try:
        claim = map_encounter_to_claim(encounter_id)
        return claim
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/reports/patients")
async def get_patients_by_month(month: str = Query(..., regex="^\\d{4}-\\d{2}$")):
    """Get patients registered in a specific month (YYYY-MM format)"""
    filtered_patients = [
        patient.dict() for patient in patients.values()
        if filter_by_month(patient.created_at[:7], month)
    ]
    
    return filtered_patients

@app.get("/reports/encounters")
async def get_encounters_by_month(
    month: str = Query(..., regex="^\\d{4}-\\d{2}$"),
    diagnosis: str = None
):
    """Get encounters recorded in a specific month with optional diagnosis filter"""
    filtered_encounters = []
    
    for patient_encounters in encounters.values():
        for encounter in patient_encounters:
            if filter_by_month(encounter.visit_date[:7], month):
                enc_dict = encounter.dict()
                # Add patient name for display
                if encounter.patient_id in patients:
                    enc_dict["patient_name"] = patients[encounter.patient_id].full_name
                if diagnosis is None or diagnosis.lower() in encounter.diagnosis.lower():
                    filtered_encounters.append(enc_dict)
    
    return filtered_encounters

@app.get("/reports/claims")
async def get_claims_by_month(
    month: str = Query(..., regex="^\\d{4}-\\d{2}$"),
    status: str = None
):
    """Get claims submitted in a specific month with optional status filter"""
    filtered_claims = [
        claim.dict() for claim in claims.values()
        if filter_by_month(claim.created[:7], month) and
        (status is None or claim.status == status)
    ]
    
    # Enhance claims with patient and encounter details
    for claim in filtered_claims:
        patient_ref = claim["patient"]["reference"]
        patient_id = patient_ref.split("/")[-1]
        if patient_id in patients:
            claim["patient_name"] = patients[patient_id].full_name
    
    return filtered_claims

@app.get("/reports/months")
async def get_available_months():
    """Get a list of months that have data"""
    all_dates = set()
    
    # Collect dates from patients
    for patient in patients.values():
        all_dates.add(patient.created_at[:7])
    
    # Collect dates from encounters
    for patient_encounters in encounters.values():
        for encounter in patient_encounters:
            all_dates.add(encounter.visit_date[:7])
    
    # Collect dates from claims
    for claim in claims.values():
        all_dates.add(claim.created[:7])
    
    return sorted(list(all_dates), reverse=True)

@app.get("/stats")
async def get_system_stats():
    """Get current system statistics"""
    return {
        "total_patients": len(patients),
        "total_encounters": sum(len(e) for e in encounters.values()),
        "total_claims": len(claims),
        "last_updated": datetime.now().isoformat()
    }

@app.post("/reset")
async def reset_system():
    """Reset all system data"""
    patients.clear()
    encounters.clear()
    claims.clear()
    return {"status": "success", "message": "All data has been reset"}

# Enhanced error handling for existing endpoints
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
