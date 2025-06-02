import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="OpenMRS-OpenIMIS Integration",
    page_icon="🏥",
    layout="wide"
)

def fetch_patients():
    try:
        response = requests.get("http://localhost:8000/patients")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def register_patient():
    st.header("Patient Registration")
    st.write("Enter patient information below")

    # Create the form
    with st.form("patient_registration_form"):
        full_name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        chief_complaint = st.text_area("Chief Complaint")

        # Submit button
        submitted = st.form_submit_button("Register Patient")

        if submitted:
            if not full_name or not chief_complaint:
                st.error("Please fill in all required fields.")
                return

            # Prepare the data
            patient_data = {
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "chief_complaint": chief_complaint
            }

            try:
                # Send the data to the backend
                response = requests.post(
                    "http://localhost:8000/patient",
                    json=patient_data
                )

                if response.status_code == 201:
                    result = response.json()
                    st.success("Patient registered successfully!")
                    
                    # Display the patient information
                    st.subheader("Patient Details:")
                    st.json(result["data"])
                else:
                    st.error(f"Error: {response.status_code}")
                    st.write(response.text)

            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server. Please ensure it is running.")

def record_encounter():
    st.header("Record Medical Encounter")
    st.write("Record a new medical encounter for an existing patient")

    # Fetch existing patients
    patients = fetch_patients()
    
    if not patients:
        st.warning("No patients found in the system. Please register a patient first.")
        return

    # Create the form
    with st.form("encounter_form"):
        # Create a dictionary of patient names to IDs for the selectbox
        patient_options = {f"{p['full_name']} (ID: {p['patient_id']})": p['patient_id'] for p in patients}
        selected_patient = st.selectbox("Select Patient", options=list(patient_options.keys()))
        
        # Get the patient ID from the selection
        patient_id = patient_options[selected_patient]

        visit_date = st.date_input("Date of Visit", value=datetime.now())
        diagnosis = st.text_area("Diagnosis")
        treatment = st.text_area("Prescribed Treatment/Medications")
        attending_clinician = st.text_input("Attending Clinician (optional)")

        submitted = st.form_submit_button("Record Encounter")

        if submitted:
            if not diagnosis or not treatment:
                st.error("Please fill in all required fields.")
                return

            # Prepare the encounter data
            encounter_data = {
                "patient_id": patient_id,
                "diagnosis": diagnosis,
                "treatment": treatment,
                "visit_date": visit_date.isoformat(),
                "attending_clinician": attending_clinician if attending_clinician else None
            }

            try:
                # Send the data to the backend
                response = requests.post(
                    "http://localhost:8000/encounter",
                    json=encounter_data
                )

                if response.status_code == 201:
                    result = response.json()
                    st.success("Medical encounter recorded successfully!")
                    
                    # Display the encounter information
                    st.subheader("Encounter Details:")
                    st.json(result["data"])
                else:
                    st.error(f"Error: {response.status_code}")
                    st.write(response.text)

            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server. Please ensure it is running.")

def view_patient_history():
    st.header("Patient History")
    st.write("View medical encounters for a patient")

    # Fetch existing patients
    patients = fetch_patients()
    
    if not patients:
        st.warning("No patients found in the system.")
        return

    # Create a dictionary of patient names to IDs for the selectbox
    patient_options = {f"{p['full_name']} (ID: {p['patient_id']})": p['patient_id'] for p in patients}
    selected_patient = st.selectbox("Select Patient", options=list(patient_options.keys()), key="history_select")
    
    if selected_patient:
        patient_id = patient_options[selected_patient]
        try:
            # Fetch patient encounters
            response = requests.get(f"http://localhost:8000/encounter/{patient_id}")
            
            if response.status_code == 200:
                encounters = response.json()
                if encounters:
                    for encounter in encounters:
                        with st.expander(f"Visit Date: {encounter['visit_date']}"):
                            st.write(f"**Diagnosis:** {encounter['diagnosis']}")
                            st.write(f"**Treatment:** {encounter['treatment']}")
                            if encounter['attending_clinician']:
                                st.write(f"**Clinician:** {encounter['attending_clinician']}")
                            st.write(f"**Encounter ID:** {encounter['encounter_id']}")
                else:
                    st.info("No encounters recorded for this patient yet.")
            else:
                st.error("Error fetching patient encounters")
        
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend server. Please ensure it is running.")

def submit_claim():
    st.header("Submit Insurance Claim")
    st.write("Generate and submit a FHIR Claim from an existing encounter")

    # Fetch available encounters
    try:
        response = requests.get("http://localhost:8000/encounters")
        if response.status_code != 200:
            st.error("Failed to fetch encounters")
            return
        encounters = response.json()
        
        if not encounters:
            st.warning("No encounters found in the system. Please record an encounter first.")
            return
        
        # Create encounter selection dropdown
        encounter_options = {
            f"{enc['patient_name']} - {enc['visit_date']} ({enc['diagnosis']})": enc['encounter_id']
            for enc in encounters
        }
        
        selected_encounter = st.selectbox(
            "Select Encounter",
            options=list(encounter_options.keys()),
            help="Choose the encounter to generate a claim for"
        )
        
        if selected_encounter:
            encounter_id = encounter_options[selected_encounter]
            
            # Get the FHIR Claim preview
            try:
                # First get the full encounter data
                encounter_response = requests.get(f"http://localhost:8000/encounters/{encounter_id}")
                if encounter_response.status_code != 200:
                    st.error("Failed to fetch encounter details")
                    return
                
                # Then get the mapped claim
                claim_response = requests.get(
                    f"http://localhost:8000/encounters/{encounter_id}/claim"
                )
                if claim_response.status_code != 200:
                    st.error("Failed to generate claim preview")
                    return
                
                claim_data = claim_response.json()
                
                # Display the claim preview
                st.subheader("FHIR Claim Preview")
                with st.expander("View Complete Claim JSON", expanded=True):
                    st.json(claim_data)
                
                # Add a submit button
                if st.button("Submit Claim"):
                    try:
                        submit_response = requests.post(
                            "http://localhost:8000/claim",
                            json=claim_data
                        )
                        
                        if submit_response.status_code == 201:
                            result = submit_response.json()
                            st.success("Claim submitted successfully!")
                            st.json(result)
                        else:
                            st.error(f"Error submitting claim: {submit_response.status_code}")
                            st.write(submit_response.text)
                    
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the backend server.")
                
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server.")
    
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server.")

def view_monthly_report():
    st.header("Monthly Report")
    st.write("View consolidated data for a specific month")

    # Fetch available months
    try:
        months_response = requests.get("http://localhost:8000/reports/months")
        if months_response.status_code != 200:
            st.error("Failed to fetch available months")
            return
        
        available_months = months_response.json()
        if not available_months:
            st.warning("No data available for reporting")
            return
        
        # Month selection
        selected_month = st.selectbox(
            "Select Reporting Month",
            options=available_months,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B %Y")
        )
        
        # Fetch data for the selected month
        with st.spinner("Loading report data..."):
            # Get patients
            patients_response = requests.get(f"http://localhost:8000/reports/patients?month={selected_month}")
            if patients_response.status_code != 200:
                st.error("Failed to fetch patient data")
                return
            patients_data = patients_response.json()
            
            # Get encounters with optional diagnosis filter
            diagnosis_filter = st.text_input("Filter by Diagnosis (optional)", "")
            encounters_url = f"http://localhost:8000/reports/encounters?month={selected_month}"
            if diagnosis_filter:
                encounters_url += f"&diagnosis={diagnosis_filter}"
            encounters_response = requests.get(encounters_url)
            if encounters_response.status_code != 200:
                st.error("Failed to fetch encounter data")
                return
            encounters_data = encounters_response.json()
            
            # Get claims
            claims_response = requests.get(f"http://localhost:8000/reports/claims?month={selected_month}")
            if claims_response.status_code != 200:
                st.error("Failed to fetch claims data")
                return
            claims_data = claims_response.json()
            
            # Display aggregate metrics
            st.subheader("Monthly Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("New Patients", len(patients_data))
            with col2:
                st.metric("Total Encounters", len(encounters_data))
            with col3:
                st.metric("Claims Submitted", len(claims_data))
            
            # Calculate financial metrics
            total_amount = sum(float(claim.get("total", {}).get("value", 0)) for claim in claims_data)
            accepted_claims = sum(1 for claim in claims_data if claim.get("status") == "accepted")
            
            col4, col5 = st.columns(2)
            with col4:
                st.metric("Total Billed Amount (USD)", f"${total_amount:,.2f}")
            with col5:
                st.metric("Accepted Claims", f"{accepted_claims}/{len(claims_data)}")
            
            # Display detailed tables
            st.markdown("---")
            
            # Patients table
            st.subheader("New Patient Registrations")
            if patients_data:
                patients_df = pd.DataFrame(patients_data)
                patients_df = patients_df[["patient_id", "full_name", "created_at"]]
                patients_df.columns = ["Patient ID", "Full Name", "Registration Date"]
                st.dataframe(patients_df)
            else:
                st.info("No new patients registered this month")
            
            # Encounters table
            st.subheader("Medical Encounters")
            if encounters_data:
                encounters_df = pd.DataFrame(encounters_data)
                encounters_df = encounters_df[["encounter_id", "patient_name", "visit_date", "diagnosis", "treatment", "attending_clinician"]]
                encounters_df.columns = ["Encounter ID", "Patient Name", "Visit Date", "Diagnosis", "Treatment", "Clinician"]
                st.dataframe(encounters_df)
            else:
                st.info("No encounters recorded this month")
            
            # Claims table
            st.subheader("Insurance Claims")
            if claims_data:
                # Extract relevant fields from nested claim structure
                claims_list = []
                for claim in claims_data:
                    claims_list.append({
                        "Claim ID": claim.get("id", ""),
                        "Patient Name": claim.get("patient_name", ""),
                        "Date Submitted": claim.get("created", ""),
                        "Status": claim.get("status", ""),
                        "Amount": claim.get("total", {}).get("value", 0)
                    })
                claims_df = pd.DataFrame(claims_list)
                st.dataframe(claims_df)
            else:
                st.info("No claims submitted this month")
    
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server. Please ensure it is running.")

def main():
    st.title("OpenMRS-OpenIMIS Integration")
    
    # Create a navigation menu
    menu = ["Patient Registration", "Record Encounter", "View Patient History", "Submit Claim", "Monthly Report"]
    choice = st.sidebar.selectbox("Select Action", menu)
    
    if choice == "Patient Registration":
        register_patient()
    elif choice == "Record Encounter":
        record_encounter()
    elif choice == "Submit Claim":
        submit_claim()
    elif choice == "Monthly Report":
        view_monthly_report()
    else:
        view_patient_history()

if __name__ == "__main__":
    main()
