import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Automatically determine the root directory and add it to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.optimization_pyomo import mip_optimization_with_data

# Streamlit UI title and description
st.title("Optimization with Pyomo")
st.write("Upload a CSV file and trigger the optimization.")

# Initialize session state for file path and optimization data
if "file_path" not in st.session_state:
    st.session_state.file_path = None
if "optimized_data" not in st.session_state:
    st.session_state.optimized_data = None

# File upload widget
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    st.session_state.file_path = os.path.join("uploads", uploaded_file.name)

    # Save uploaded file
    with open(st.session_state.file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"File uploaded successfully: {uploaded_file.name}")

    # Display a preview of the uploaded data
    data = pd.read_csv(st.session_state.file_path)
    st.write("### Preview of Uploaded Data:")
    st.write(data.head())

# Button to trigger the optimization
if st.button("Run Optimization"):
    if st.session_state.file_path:
        optimized_file = mip_optimization_with_data(st.session_state.file_path)
        if optimized_file:
            st.success("Optimization complete!")
            st.session_state.optimized_data = pd.read_csv(optimized_file)

            # Provide a download link for results
            with open(optimized_file, "rb") as file:
                st.download_button(
                    label="Download Optimized Data",
                    data=file,
                    file_name="optimized_data.csv",
                    mime="text/csv"
                )
        else:
            st.error("No optimal solution found. Please review your data or constraints.")
    else:
        st.error("Please upload a file first.")

# Display the visualizations only if optimization results exist
if st.session_state.optimized_data is not None:
    optimized_data = st.session_state.optimized_data
    wave_columns = [col for col in optimized_data.columns if "Wave" in col]
    melted_data = optimized_data.melt(id_vars=['Property', 'Owner', 'Manager'],
                                      value_vars=wave_columns,
                                      var_name="Wave",
                                      value_name="Assigned")

    # Filter only assigned properties
    assigned_data = melted_data[melted_data['Assigned'] == 1]

    # Total Assignments Per Wave with sorted order
    total_assignments = assigned_data.groupby("Wave").size().reset_index(name="Total Assignments")
    wave_order = sorted(total_assignments['Wave'].unique(), key=lambda x: int(x.replace('Wave', '')))
    total_assignments['Wave'] = pd.Categorical(total_assignments['Wave'], categories=wave_order, ordered=True)
    total_assignments = total_assignments.sort_values('Wave')

    fig_total = px.bar(
        total_assignments,
        x="Wave",
        y="Total Assignments",
        title="Total Properties Assigned per Wave"
    )
    st.plotly_chart(fig_total)

    # Total Assignments Per Owner with sorted order
    selected_owner = st.selectbox("Select Owner to View Assignments", options=assigned_data['Owner'].unique())
    owner_data = assigned_data[assigned_data['Owner'] == selected_owner]
    owner_assignments = owner_data.groupby("Wave").size().reset_index(name="Total Assignments")
    owner_assignments['Wave'] = pd.Categorical(owner_assignments['Wave'], categories=wave_order, ordered=True)
    owner_assignments = owner_assignments.sort_values('Wave')

    fig_owner = px.bar(
        owner_assignments,
        x="Wave",
        y="Total Assignments",
        title=f"Total Assignments for {selected_owner} per Wave",
        color_discrete_sequence=["orange"]
    )
    st.plotly_chart(fig_owner)

    # Total Assignments Per Manager with sorted order
    selected_manager = st.selectbox("Select Manager to View Assignments", options=assigned_data['Manager'].unique())
    manager_data = assigned_data[assigned_data['Manager'] == selected_manager]
    manager_assignments = manager_data.groupby("Wave").size().reset_index(name="Total Assignments")
    manager_assignments['Wave'] = pd.Categorical(manager_assignments['Wave'], categories=wave_order, ordered=True)
    manager_assignments = manager_assignments.sort_values('Wave')

    fig_manager = px.bar(
        manager_assignments,
        x="Wave",
        y="Total Assignments",
        title=f"Total Assignments for {selected_manager} per Wave",
        color_discrete_sequence=["green"]
    )
    st.plotly_chart(fig_manager)
