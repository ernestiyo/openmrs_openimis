import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date, timedelta

# Constants
BASE_URL = "http://localhost:8000"

# Configure the page with consistent styling
st.set_page_config(
    page_title="OpenMRS-OpenIMIS Integration",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper Functions
def make_request(method, endpoint, data=None, params=None):
    """Centralized request handling with error management"""
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.request(method, url, json=data, params=params)
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the backend server. Please ensure it is running.")
        return None

def fetch_patients():
    """Fetch all patients with error handling"""
    response = make_request("GET", "patients")
    if response and response.status_code == 200:
        return response.json()
    return []

def fetch_encounters():
    """Fetch all encounters with error handling"""
    response = make_request("GET", "encounters")
    if response and response.status_code == 200:
        return response.json()
    return []

def fetch_claims():
    """Fetch all claims with error handling"""
    response = make_request("GET", "claims")
    if response and response.status_code == 200:
        return response.json()
    return []

def generate_month_options(months_back=12):
    """Generate a list of recent months for reporting"""
    today = date.today()
    months = []
    for i in range(months_back):
        current = today.replace(day=1) - timedelta(days=i*30)
        months.append(current.strftime("%Y-%m"))
    return sorted(months, reverse=True)

def apply_custom_css():
    """Apply custom CSS for consistent styling"""
    st.markdown("""
        <style>
        .main .block-container { padding-top: 2rem; }
        h1 { margin-bottom: 2rem; }
        .stAlert { margin-top: 1rem; }
        .row-widget.stButton { margin-top: 1rem; }
        </style>
    """, unsafe_allow_html=True)

def confirm_action(message="Are you sure?", confirmation_text="YES"):
    """Reusable confirmation dialog"""
    col1, col2 = st.columns([3, 1])
    with col1:
        user_confirmation = st.text_input(
            f'{message} Type "{confirmation_text}" to confirm:',
            key=f"confirm_{message}"
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        return st.button("Confirm", disabled=user_confirmation != confirmation_text)

def show_register_patient():
    st.header("🧑‍⚕️ Patient Registration")
    st.write("Enter new patient information below")

    with st.form("patient_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input(
                "Full Name",
                placeholder="Enter patient's full name",
                help="Required: Patient's complete name as it appears on ID"
            )
        with col2:
            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                help="Required: Patient's current age"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            gender = st.selectbox(
                "Gender",
                options=["", "Male", "Female", "Other"],
                help="Required: Patient's gender"
            )
        with col4:
            st.write("") # Spacing for alignment
        
        chief_complaint = st.text_area(
            "Chief Complaint",
            placeholder="Describe the main reason for visit",
            help="Required: Primary reason the patient is seeking care"
        )

        submitted = st.form_submit_button("🆕 Register Patient")

        if submitted:
            if not full_name or not chief_complaint or not gender:
                st.error("❌ Please fill in all required fields.")
                return

            patient_data = {
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "chief_complaint": chief_complaint
            }

            response = make_request("POST", "patient", data=patient_data)
            if response and response.status_code == 201:
                result = response.json()
                st.success("✅ Patient registered successfully!")
                
                with st.expander("View Patient Details", expanded=True):
                    st.json(result["data"])

def show_record_encounter():
    st.header("📝 Record Medical Encounter")
    st.write("Record a new medical encounter for an existing patient")

    patients = fetch_patients()
    if not patients:
        st.warning("⚠️ No patients found in the system. Please register a patient first.")
        if st.button("Go to Patient Registration"):
            st.session_state.app_section = "Register Patient"
            st.experimental_rerun()
        return

    with st.form("encounter_form", clear_on_submit=True):
        # Patient selection with search
        patient_options = {
            f"{p['full_name']} (ID: {p['patient_id']})": p['patient_id']
            for p in patients
        }
        selected_patient = st.selectbox(
            "Select Patient",
            options=list(patient_options.keys()),
            help="Choose the patient for this encounter"
        )
        
        patient_id = patient_options[selected_patient]

        col1, col2 = st.columns(2)
        with col1:
            visit_date = st.date_input(
                "Date of Visit",
                value=datetime.now(),
                max_value=date.today()
            )
        with col2:
            attending_clinician = st.text_input(
                "Attending Clinician",
                placeholder="Enter clinician's name (optional)"
            )

        diagnosis = st.text_area(
            "Diagnosis",
            placeholder="Enter detailed diagnosis",
            help="Required: Medical diagnosis for this visit"
        )
        
        treatment = st.text_area(
            "Prescribed Treatment/Medications",
            placeholder="Enter prescribed treatment and medications",
            help="Required: Treatment plan and medications"
        )

        submitted = st.form_submit_button("💾 Record Encounter")

        if submitted:
            if not diagnosis or not treatment:
                st.error("❌ Please fill in all required fields.")
                return

            encounter_data = {
                "patient_id": patient_id,
                "diagnosis": diagnosis,
                "treatment": treatment,
                "visit_date": visit_date.isoformat(),
                "attending_clinician": attending_clinician if attending_clinician else None
            }

            response = make_request("POST", "encounter", data=encounter_data)
            if response and response.status_code == 201:
                result = response.json()
                st.success("✅ Medical encounter recorded successfully!")
                
                with st.expander("View Encounter Details", expanded=True):
                    st.json(result["data"])

def show_submit_claim():
    st.header("💰 Submit Insurance Claim")
    st.write("Generate and submit a FHIR Claim from an existing encounter")

    encounters = fetch_encounters()
    if not encounters:
        st.warning("⚠️ No encounters found in the system. Please record an encounter first.")
        if st.button("Go to Record Encounter"):
            st.session_state.app_section = "Record Encounter"
            st.experimental_rerun()
        return

    # Search/filter encounters
    search_term = st.text_input(
        "🔍 Search Encounters",
        placeholder="Search by patient name or diagnosis"
    ).lower()

    filtered_encounters = encounters
    if search_term:
        filtered_encounters = [
            enc for enc in encounters
            if search_term in enc['patient_name'].lower() or
               search_term in enc['diagnosis'].lower()
        ]

    if not filtered_encounters:
        st.info("No encounters match your search criteria.")
        return

    encounter_options = {
        f"{enc['patient_name']} - {enc['visit_date']} ({enc['diagnosis']})": enc['encounter_id']
        for enc in filtered_encounters
    }

    selected_encounter = st.selectbox(
        "Select Encounter",
        options=list(encounter_options.keys()),
        help="Choose the encounter to generate a claim for"
    )

    if selected_encounter:
        encounter_id = encounter_options[selected_encounter]
        
        # Get the FHIR Claim preview
        claim_response = make_request("GET", f"encounters/{encounter_id}/claim")
        if claim_response and claim_response.status_code == 200:
            claim_data = claim_response.json()
            
            st.subheader("📋 FHIR Claim Preview")
            with st.expander("View Complete Claim JSON", expanded=True):
                st.json(claim_data)
            
            if st.button("📤 Submit Claim"):
                submit_response = make_request("POST", "claim", data=claim_data)
                if submit_response and submit_response.status_code == 201:
                    result = submit_response.json()
                    st.success("✅ Claim submitted successfully!")
                    st.json(result)

def show_monthly_report():
    st.header("📊 Monthly Report")
    st.write("View consolidated data and statistics for a specific month")

    # Get available months
    months_response = make_request("GET", "reports/months")
    if not months_response or months_response.status_code != 200:
        st.error("❌ Failed to fetch available months")
        return

    available_months = months_response.json()
    if not available_months:
        st.warning("⚠️ No data available for reporting")
        return

    # Report controls
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_month = st.selectbox(
            "Select Reporting Month",
            options=available_months,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B %Y")
        )
    
    with col2:
        st.write("")  # Spacing
        if st.button("🔄 Refresh Data"):
            st.experimental_rerun()

    # Fetch and display data
    with st.spinner("📊 Loading report data..."):
        # Get all data for the month
        patients_data = make_request("GET", f"reports/patients?month={selected_month}").json()
        
        diagnosis_filter = st.text_input("🔍 Filter by Diagnosis", "")
        encounters_url = f"reports/encounters?month={selected_month}"
        if diagnosis_filter:
            encounters_url += f"&diagnosis={diagnosis_filter}"
        encounters_data = make_request("GET", encounters_url).json()
        
        claims_data = make_request("GET", f"reports/claims?month={selected_month}").json()
        
        # Display metrics
        st.subheader("📈 Monthly Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🧑‍⚕️ New Patients", len(patients_data))
        with col2:
            st.metric("📝 Total Encounters", len(encounters_data))
        with col3:
            st.metric("💰 Claims Submitted", len(claims_data))
        
        total_amount = sum(float(claim.get("total", {}).get("value", 0)) for claim in claims_data)
        accepted_claims = sum(1 for claim in claims_data if claim.get("status") == "accepted")
        
        col4, col5 = st.columns(2)
        with col4:
            st.metric("💵 Total Billed Amount", f"${total_amount:,.2f}")
        with col5:
            st.metric("✅ Accepted Claims", f"{accepted_claims}/{len(claims_data)}")
        
        # Display detailed tables
        st.markdown("---")
        
        # Patients table
        st.subheader("🧑‍⚕️ New Patient Registrations")
        if patients_data:
            patients_df = pd.DataFrame([{
                "Patient ID": p["patient_id"],
                "Full Name": p["full_name"],
                "Registration Date": p["created_at"],
                "Age": p["age"],
                "Gender": p["gender"]
            } for p in patients_data])
            st.dataframe(patients_df, use_container_width=True)
        else:
            st.info("No new patients registered this month")
        
        # Encounters table
        st.subheader("📝 Medical Encounters")
        if encounters_data:
            encounters_df = pd.DataFrame([{
                "Encounter ID": e["encounter_id"],
                "Patient Name": e["patient_name"],
                "Visit Date": e["visit_date"],
                "Diagnosis": e["diagnosis"],
                "Treatment": e["treatment"],
                "Clinician": e["attending_clinician"] or "N/A"
            } for e in encounters_data])
            st.dataframe(encounters_df, use_container_width=True)
        else:
            st.info("No encounters recorded this month")
        
        # Claims table
        st.subheader("💰 Insurance Claims")
        if claims_data:
            claims_list = [{
                "Claim ID": claim.get("id", ""),
                "Patient Name": claim.get("patient_name", ""),
                "Date Submitted": claim.get("created", ""),
                "Status": claim.get("status", ""),
                "Amount": f"${float(claim.get('total', {}).get('value', 0)):,.2f}"
            } for claim in claims_data]
            claims_df = pd.DataFrame(claims_list)
            st.dataframe(claims_df, use_container_width=True)
        else:
            st.info("No claims submitted this month")

def show_administration():
    st.header("⚙️ Administration")
    st.write("System management and statistics")

    # Runtime statistics
    stats_response = make_request("GET", "stats")
    if stats_response and stats_response.status_code == 200:
        stats = stats_response.json()
        
        st.subheader("📊 System Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients", stats["total_patients"])
        with col2:
            st.metric("Total Encounters", stats["total_encounters"])
        with col3:
            st.metric("Total Claims", stats["total_claims"])
    
    st.markdown("---")
    
    # Data reset section
    st.subheader("⚠️ Danger Zone")
    st.warning("The following actions cannot be undone!")
    
    if confirm_action(
        message="Reset all system data?",
        confirmation_text="RESET"
    ):
        response = make_request("POST", "reset")
        if response and response.status_code == 200:
            st.success("✅ All data has been reset successfully!")
            st.button("Refresh Page", on_click=st.experimental_rerun)

def main():
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state for navigation
    if 'app_section' not in st.session_state:
        st.session_state.app_section = "Register Patient"
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🏥 Clinic Middleware")
        st.markdown("---")
        
        sections = {
            "Register Patient": "🧑‍⚕️",
            "Record Encounter": "📝",
            "Submit Claim": "💰",
            "Monthly Report": "📊",
            "Administration": "⚙️"
        }
        
        selected_section = st.radio(
            "Navigation",
            options=list(sections.keys()),
            format_func=lambda x: f"{sections[x]} {x}",
            key="nav_radio"
        )
        st.session_state.app_section = selected_section
    
    # Main content
    if st.session_state.app_section == "Register Patient":
        show_register_patient()
    elif st.session_state.app_section == "Record Encounter":
        show_record_encounter()
    elif st.session_state.app_section == "Submit Claim":
        show_submit_claim()
    elif st.session_state.app_section == "Monthly Report":
        show_monthly_report()
    else:
        show_administration()

if __name__ == "__main__":
    main()
