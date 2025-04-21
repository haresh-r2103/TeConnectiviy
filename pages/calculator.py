import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import os
from utils.cost_formulas import (calculate_storage_cost,
                                 calculate_compute_cost, calculate_dbu_cost,
                                 calculate_photon_cost)

# Set page config with professional color scheme
st.set_page_config(page_title="Databricks Cloud Cost Calculator",
                   page_icon="",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Custom CSS for better visibility
st.markdown("""
    <style>
        :root {
            --primary-color: #FF8200;
            --secondary-color: #6c757d;
            --background-color: #f5f5f5;
            --card-color: #ffffff;
            --text-color: #333333;
            --success-color: #28a745;
        }
        .main {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        .header {
            color: var(--primary-color);
            font-weight: bold;
        }
        .cost-card {
            border-left: 4px solid var(--primary-color);
            padding: 12px;
            margin: 8px 0;
            background-color: var(--card-color);
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .cost-card:hover {
            transform: translateY(-2px);
        }
        .total-card {
            background-color: var(--card-color);
            padding: 16px;
            border-radius: 4px;
            margin: 16px 0;
            border: 1px solid var(--primary-color);
        }
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .stNumberInput, .stTextInput, .stSelectbox {
            margin-bottom: 15px;
        }
        .tab-content {
            padding: 15px;
            background-color: var(--card-color);
            border-radius: 5px;
            margin-top: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .layer-tabs {
            margin-bottom: 20px;
        }
        .cost-badge {
            display: inline-block;
            padding: 0.25em 0.4em;
            font-size: 75%;
            font-weight: 700;
            line-height: 1;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.25rem;
            background-color: var(--primary-color);
            color: white;
        }
        .stButton>button {
            background-color: var(--primary-color);
            color: white;
        }
        .stButton>button:hover {
            background-color: #e67600;
            color: white;
        }
        .success-badge {
            background-color: var(--success-color);
        }
        .summary-header {
            background-color: var(--primary-color);
            color: white;
            padding: 10px 15px;
            border-radius: 4px 4px 0 0;
            font-weight: bold;
        }
        .summary-body {
            background-color: white;
            padding: 15px;
            border-radius: 0 0 4px 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info-tooltip {
            font-size: 16px;
            color: var(--primary-color);
            margin-left: 5px;
            cursor: help;
        }
        .photon-card {
            background: linear-gradient(to right, #f8f9fa, #e9ecef);
            border-left: 4px solid #007bff;
            padding: 12px;
            margin: 12px 0;
            border-radius: 4px;
        }
        .back-button {
            display: inline-flex;
            align-items: center;
            color: var(--primary-color);
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px 10px;
            font-size: 14px;
            transition: color 0.2s;
            text-decoration: none;
        }
        .back-button:hover {
            color: #e67600;
        }
        .back-button svg {
            margin-right: 5px;
        }
    </style>
""",
            unsafe_allow_html=True)

# Add back button to home
st.markdown("""
<a href="/" class="back-button">
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
    </svg>
    Back to Home
</a>
""",
            unsafe_allow_html=True)

# Logo placement at the top
logo_path = "logo.png"
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(logo, width=200)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning(
        "Logo image not found. Please ensure 'logo.png' is in the same directory."
    )

# Cost constants (AWS only)
COSTS = {
    "S3": {
        "Standard": 0.023,
        "Intelligent-Tiering": 0.022,
        "Standard-IA": 0.0125,
        "OneZone-IA": 0.01,
        "Glacier": 0.004,
        "GlacierDeep": 0.00099
    },
    "EC2": {
        "i3.xlarge": 0.312,
        "i3.2xlarge": 0.624,
        "i3.4xlarge": 1.248,
        "i3.8xlarge": 2.496,
        "i3.16xlarge": 4.992,
        "r5.xlarge": 0.252,
        "r5.2xlarge": 0.504,
        "r5.4xlarge": 1.008,
        "r5.8xlarge": 2.016,
        "r5.12xlarge": 3.024
    },
    "DBU": {
        "Enterprise": 0.75,
        "DLT_Advanced": 0.36,
        "DLT_Core": 0.20,
        "DLT_Pro": 0.25,
        "Jobs": 0.15
    },
    "Photon": {
        "acceleration_factor": 0.2  # 20% of base compute cost
    }
}

# Default compute configuration (hidden from user)
DEFAULT_COMPUTE = {
    "instance_type": "r5.xlarge",
    "num_instances": 2,
    "hours_per_day": 8,
    "days_per_month": 22
}

# Main app
st.markdown('<h1 class="header">Databricks Cloud Cost Calculator</h1>',
            unsafe_allow_html=True)
st.markdown("""
    Estimate your AWS costs for Databricks deployments. Configure each layer below.
""")

# Initialize session state for storing all costs
if 'all_costs' not in st.session_state:
    st.session_state.all_costs = {
        "Landing": {},
        "RAW": {},
        "CONF": {},
        "PB": {}
    }

# Layer tabs
layer = st.selectbox("Select Layer to Configure",
                     ["Landing", "RAW", "CONF", "PB"])

# LANDING LAYER CONFIGURATION
if layer == "Landing":
    st.subheader("Landing Layer Configuration")
    mode = st.radio("Estimation Mode", ["Simple", "Advanced"],
                    horizontal=True,
                    key="landing_mode")

    if mode == "Simple":
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            num_tables = st.number_input(
                "Number of Tables",
                min_value=1,
                value=5,
                help="Total number of tables in your landing zone")
            avg_file_size = st.number_input(
                "Average File Size (GB)",
                min_value=0.1,
                value=2.0,
                help="Average size of each file in GB")

        with col2:
            file_growth = st.number_input(
                "Monthly Growth Rate (%)",
                min_value=0,
                max_value=100,
                value=5,
                help="Expected monthly growth of your data")
            files_per_day = st.number_input(
                "Files Received Per Day",
                min_value=1,
                value=10,
                help="Average number of files received daily")

        retention = st.selectbox("Retention Policy", [
            "30 days", "60 days", "90 days", "180 days", "1 physical month",
            "2 physical months", "Indefinite"
        ],
                                 help="How long should the data be retained?")

        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate storage for Landing layer (Simple mode)
        total_files = files_per_day * 30  # Assuming 30 days in a physical month
        total_storage_gb = total_files * avg_file_size
        growth_factor = 1 + (file_growth / 100)

        # Get months from retention policy
        if "physical month" in retention:
            if retention == "1 physical month":
                retention_months = 1
            elif retention == "2 physical months":
                retention_months = 2
            else:
                retention_months = 1  # Default
        elif "days" in retention:
            days = int(retention.split()[0])
            retention_months = days / 30  # Convert days to months
        else:  # Indefinite
            retention_months = 12  # Assume 1 year for calculation

        # Calculate cost with retention
        projected_storage = total_storage_gb * (growth_factor**
                                                retention_months)
        storage_cost = calculate_storage_cost(
            projected_storage,
            COSTS["S3"][storage_type],
            months=1  # For a single physical month
        )

        # Store in session state
        st.session_state.all_costs["Landing"] = {
            "storage_gb": projected_storage,
            "storage_cost_per_month": storage_cost,
            "storage_tier": storage_type,
            "retention_policy": retention
        }

    else:  # Advanced mode
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.info("Add each landing table individually for precise estimation")

        # Initialize session state for tables if not exists
        if 'landing_tables' not in st.session_state:
            st.session_state.landing_tables = []

        # Form to add new tables
        with st.form("add_table_form"):
            col1, col2 = st.columns(2)
            with col1:
                table_name = st.text_input("Table Name",
                                           help="Unique name for this table")
                avg_file_size = st.number_input("Average File Size (GB)",
                                                min_value=0.1,
                                                value=2.0)

            with col2:
                files_per_day = st.number_input("Files Per Day",
                                                min_value=1,
                                                value=5)
                retention = st.selectbox("Retention Policy", [
                    "30 days", "60 days", "90 days", "180 days",
                    "1 physical month", "2 physical months", "Indefinite"
                ])

            if st.form_submit_button("Add Table"):
                if table_name:
                    if table_name in [
                            t['name'] for t in st.session_state.landing_tables
                    ]:
                        st.error("Table with this name already exists!")
                    else:
                        st.session_state.landing_tables.append({
                            'name':
                            table_name,
                            'avg_file_size':
                            avg_file_size,
                            'files_per_day':
                            files_per_day,
                            'retention':
                            retention
                        })
                        st.success(f"Table '{table_name}' added!")
                else:
                    st.error("Please enter a table name")

        # Display added tables
        if st.session_state.landing_tables:
            st.subheader("Your Landing Tables")
            df_tables = pd.DataFrame(st.session_state.landing_tables)
            st.dataframe(df_tables)

            if st.button("Clear All Tables"):
                st.session_state.landing_tables = []
                st.rerun()

        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate storage for Landing layer (Advanced mode)
        if st.session_state.landing_tables:
            total_storage_gb = 0
            for table in st.session_state.landing_tables:
                files_per_month = table[
                    'files_per_day'] * 30  # Assuming 30 days in a physical month
                table_storage = files_per_month * table['avg_file_size']

                # Get months from retention policy
                if "physical month" in table['retention']:
                    if table['retention'] == "1 physical month":
                        retention_months = 1
                    elif table['retention'] == "2 physical months":
                        retention_months = 2
                    else:
                        retention_months = 1  # Default
                elif "days" in table['retention']:
                    days = int(table['retention'].split()[0])
                    retention_months = days / 30  # Convert days to months
                else:  # Indefinite
                    retention_months = 12  # Assume 1 year for calculation

                # Accumulate storage with retention
                total_storage_gb += table_storage * retention_months

            storage_cost = calculate_storage_cost(
                total_storage_gb,
                COSTS["S3"][storage_type],
                months=1  # For a single physical month
            )

            # Store in session state
            st.session_state.all_costs["Landing"] = {
                "storage_gb": total_storage_gb,
                "storage_cost_per_month": storage_cost,
                "storage_tier": storage_type,
                "tables_count": len(st.session_state.landing_tables)
            }

# RAW LAYER CONFIGURATION
elif layer == "RAW":
    st.subheader("RAW Layer Configuration")
    mode = st.radio("Estimation Mode", ["Simple", "Advanced"],
                    horizontal=True,
                    key="raw_mode")

    if mode == "Simple":
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            num_jobs = st.number_input("Number of Jobs",
                                       min_value=1,
                                       value=3,
                                       help="Total number of processing jobs")
            num_tables = st.number_input(
                "Number of Tables",
                min_value=1,
                value=10,
                help="Number of tables being processed")

        with col2:
            instance_type = st.selectbox(
                "Instance Type",
                list(COSTS["EC2"].keys()),
                index=list(COSTS["EC2"].keys()).index("r5.xlarge")
                if "r5.xlarge" in COSTS["EC2"] else 0,
                help="Select the instance type for your jobs")
            avg_runs_per_month = st.number_input(
                "Average Runs per Physical Month",
                min_value=1,
                value=30,
                help="How many times each job runs per physical month")

        avg_job_duration = st.number_input(
            "Average Job Duration (minutes)",
            min_value=1,
            value=45,
            help="Average runtime duration for each job")

        enable_photon = st.checkbox(
            "Enable Photon Acceleration",
            value=True,
            help=
            "Photon is Databricks' next-generation query engine that accelerates queries"
        )

        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate costs for RAW layer (Simple mode)
        # Convert job duration to hours
        job_hours = (avg_job_duration / 60) * num_jobs * avg_runs_per_month

        # Compute cost
        compute_cost = calculate_compute_cost(
            COSTS["EC2"][instance_type],
            1,  # Number of instances per job
            job_hours / 30,  # Hours per day
            30  # Days per physical month
        )

        # Photon acceleration cost if enabled
        photon_cost = 0
        if enable_photon:
            photon_cost = calculate_photon_cost(
                compute_cost, COSTS["Photon"]["acceleration_factor"])

        # Storage estimate for processed tables in RAW
        raw_storage_gb = num_tables * 50  # Assume 50GB per table in RAW
        storage_cost = calculate_storage_cost(
            raw_storage_gb,
            COSTS["S3"][storage_type],
            months=1  # For a single physical month
        )

        # Total cost
        total_cost = compute_cost + storage_cost + photon_cost

        # Store in session state
        st.session_state.all_costs["RAW"] = {
            "compute_cost": compute_cost,
            "storage_cost": storage_cost,
            "photon_cost": photon_cost,
            "total_cost": total_cost,
            "jobs_count": num_jobs,
            "storage_gb": raw_storage_gb,
            "instance_type": instance_type,
            "photon_enabled": enable_photon
        }

    else:  # Advanced mode
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.info("Add each job individually with specific configurations")

        # Initialize session state for jobs if not exists
        if 'raw_jobs' not in st.session_state:
            st.session_state.raw_jobs = []

        # Form to add new jobs
        with st.form("add_job_form"):
            col1, col2 = st.columns(2)
            with col1:
                job_name = st.text_input("Job Name",
                                         help="Unique name for this job")
                instance_type = st.selectbox(
                    "Instance Type",
                    list(COSTS["EC2"].keys()),
                    help="Select specific instance type")

            with col2:
                avg_duration = st.number_input(
                    "Average Duration (min)",
                    min_value=1,
                    value=30,
                    help="Average runtime for this job")
                runs_per_month = st.number_input(
                    "Runs per Physical Month",
                    min_value=1,
                    value=30,
                    help="How many times this job runs monthly")

            enable_photon_job = st.checkbox(
                "Enable Photon Acceleration",
                value=True,
                help=
                "Photon is Databricks' next-generation query engine that accelerates queries"
            )

            if st.form_submit_button("Add Job"):
                if job_name:
                    if job_name in [
                            j['name'] for j in st.session_state.raw_jobs
                    ]:
                        st.error("Job with this name already exists!")
                    else:
                        st.session_state.raw_jobs.append({
                            'name':
                            job_name,
                            'instance_type':
                            instance_type,
                            'avg_duration':
                            avg_duration,
                            'runs_per_month':
                            runs_per_month,
                            'photon_enabled':
                            enable_photon_job
                        })
                        st.success(f"Job '{job_name}' added!")
                else:
                    st.error("Please enter a job name")

        # Display added jobs
        if st.session_state.raw_jobs:
            st.subheader("Your RAW Layer Jobs")

            # Create DataFrame with costs calculation
            job_data = []
            for job in st.session_state.raw_jobs:
                job_hours = (job['avg_duration'] / 60) * job['runs_per_month']
                instance_cost = COSTS["EC2"][job['instance_type']]

                # Compute cost for this job
                compute_cost = calculate_compute_cost(
                    instance_cost,
                    1,  # Number of instances per job
                    job_hours / 30,  # Hours per day
                    30  # Days per physical month
                )

                # Photon acceleration cost if enabled
                photon_cost = 0
                if job['photon_enabled']:
                    photon_cost = calculate_photon_cost(
                        compute_cost, COSTS["Photon"]["acceleration_factor"])

                job_data.append({
                    'Name':
                    job['name'],
                    'Instance':
                    job['instance_type'],
                    'Duration (min)':
                    job['avg_duration'],
                    'Runs/Physical Month':
                    job['runs_per_month'],
                    'Photon':
                    'Enabled' if job['photon_enabled'] else 'Disabled',
                    'Compute Cost ($)':
                    round(compute_cost, 2),
                    'Photon Cost ($)':
                    round(photon_cost, 2),
                    'Total Cost ($)':
                    round(compute_cost + photon_cost, 2)
                })

            df_jobs = pd.DataFrame(job_data)
            st.dataframe(df_jobs)

            if st.button("Clear All Jobs"):
                st.session_state.raw_jobs = []
                st.rerun()

        # Storage configuration
        st.subheader("RAW Layer Storage")
        estimated_tables = st.number_input(
            "Estimated Number of Tables",
            min_value=1,
            value=10,
            help="Approximate number of tables in RAW layer")
        avg_table_size = st.number_input(
            "Average Table Size (GB)",
            min_value=1.0,
            value=50.0,
            help="Average size per table in RAW layer")
        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate costs for RAW layer (Advanced mode)
        if st.session_state.raw_jobs:
            # Compute and photon costs
            total_compute_cost = 0
            total_photon_cost = 0

            for job in st.session_state.raw_jobs:
                job_hours = (job['avg_duration'] / 60) * job['runs_per_month']
                instance_cost = COSTS["EC2"][job['instance_type']]

                # Compute cost for this job
                compute_cost = calculate_compute_cost(
                    instance_cost,
                    1,  # Number of instances per job
                    job_hours / 30,  # Hours per day
                    30  # Days per physical month
                )

                # Add to total compute cost
                total_compute_cost += compute_cost

                # Photon acceleration cost if enabled
                if job['photon_enabled']:
                    photon_cost = calculate_photon_cost(
                        compute_cost, COSTS["Photon"]["acceleration_factor"])
                    total_photon_cost += photon_cost

            # Storage cost
            raw_storage_gb = estimated_tables * avg_table_size
            storage_cost = calculate_storage_cost(
                raw_storage_gb,
                COSTS["S3"][storage_type],
                months=1  # For a single physical month
            )

            # Total cost
            total_cost = total_compute_cost + storage_cost + total_photon_cost

            # Store in session state
            st.session_state.all_costs["RAW"] = {
                "compute_cost":
                total_compute_cost,
                "storage_cost":
                storage_cost,
                "photon_cost":
                total_photon_cost,
                "total_cost":
                total_cost,
                "jobs_count":
                len(st.session_state.raw_jobs),
                "storage_gb":
                raw_storage_gb,
                "photon_enabled":
                any(job['photon_enabled'] for job in st.session_state.raw_jobs)
            }

# CONF LAYER CONFIGURATION
elif layer == "CONF":
    st.subheader("CONF Layer Configuration")
    mode = st.radio("Estimation Mode", ["Simple", "Advanced"],
                    horizontal=True,
                    key="conf_mode")

    if mode == "Simple":
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            num_transforms = st.number_input(
                "Number of Transformations",
                min_value=1,
                value=4,
                help="Total number of data transformation jobs")
            dbu_per_hour = st.number_input(
                "DBUs per Hour",
                min_value=1,
                value=4,
                help="Databricks Units consumed per hour")

        with col2:
            service_tier = st.selectbox(
                "Service Tier", [
                    "Databricks Jobs", "Delta Live Tables (Core)",
                    "Delta Live Tables (Pro)", "Delta Live Tables (Advanced)"
                ],
                help="Select the appropriate Databricks service tier")
            transform_complexity = st.selectbox(
                "Transformation Complexity",
                ["Low", "Medium", "High"],
                index=1,  # Default to Medium
                help="Complexity affects storage and computing requirements")

        avg_transform_duration = st.number_input(
            "Average Transformation Duration (minutes)",
            min_value=1,
            value=60,
            help="Average runtime for transformations")
        avg_runs_per_month = st.number_input(
            "Average Runs per Physical Month",
            min_value=1,
            value=30,
            help="How many times each transformation runs monthly")
        enable_photon = st.checkbox(
            "Enable Photon Acceleration",
            value=True,
            help=
            "Photon is Databricks' next-generation query engine that accelerates queries"
        )
        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate costs for CONF layer (Simple mode)
        # Map service tier to DBU type and cost
        dbu_type_map = {
            "Databricks Jobs": "Jobs",
            "Delta Live Tables (Core)": "DLT_Core",
            "Delta Live Tables (Pro)": "DLT_Pro",
            "Delta Live Tables (Advanced)": "DLT_Advanced"
        }
        dbu_type = dbu_type_map.get(service_tier, "Jobs")
        dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Jobs"])

        # Calculate hours for all transformations in a physical month
        monthly_hours = (avg_transform_duration /
                         60) * num_transforms * avg_runs_per_month

        # Calculate compute cost
        compute_cost = calculate_dbu_cost(
            dbu_cost,
            1,  # Cluster size (already factored into dbu_per_hour)
            monthly_hours / 30,  # Hours per day
            30,  # Days per physical month
            dbu_per_hour)

        # Photon acceleration cost if enabled
        photon_cost = 0
        if enable_photon:
            photon_cost = calculate_photon_cost(
                compute_cost, COSTS["Photon"]["acceleration_factor"])

        # Storage calculation based on complexity
        complexity_factor = {
            "Low": 0.7,
            "Medium": 1.0,
            "High": 1.5
        }.get(transform_complexity, 1.0)

        conf_storage_gb = num_transforms * 50 * complexity_factor
        storage_cost = calculate_storage_cost(
            conf_storage_gb,
            COSTS["S3"][storage_type],
            months=1  # For a single physical month
        )

        # Total cost
        total_cost = compute_cost + storage_cost + photon_cost

        # Store in session state
        st.session_state.all_costs["CONF"] = {
            "compute_cost": compute_cost,
            "storage_cost": storage_cost,
            "photon_cost": photon_cost,
            "total_cost": total_cost,
            "transforms_count": num_transforms,
            "storage_gb": conf_storage_gb,
            "service_tier": service_tier,
            "photon_enabled": enable_photon
        }

    else:  # Advanced mode
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.info(
            "Add each transformation individually with specific configurations"
        )

        # Initialize session state for transformations if not exists
        if 'conf_transforms' not in st.session_state:
            st.session_state.conf_transforms = []

        # Form to add new transformations
        with st.form("add_transform_form"):
            col1, col2 = st.columns(2)
            with col1:
                transform_name = st.text_input(
                    "Transformation Name",
                    help="Unique name for this transformation")
                service_tier = st.selectbox(
                    "Service Tier", [
                        "Databricks Jobs", "Delta Live Tables (Core)",
                        "Delta Live Tables (Pro)",
                        "Delta Live Tables (Advanced)"
                    ],
                    help="Select the appropriate Databricks service tier")

            with col2:
                avg_duration = st.number_input(
                    "Average Duration (min)",
                    min_value=1,
                    value=60,
                    help="Average runtime for this transformation")
                runs_per_month = st.number_input(
                    "Runs per Physical Month",
                    min_value=1,
                    value=30,
                    help="How many times this transformation runs monthly")

            dbu_per_hour = st.number_input(
                "DBUs per Hour",
                min_value=1,
                value=4,
                help="Databricks Units consumed per hour")
            estimated_storage = st.number_input(
                "Estimated Storage (GB)",
                min_value=1.0,
                value=50.0,
                help="Estimated storage for this transformation's output")
            enable_photon_transform = st.checkbox(
                "Enable Photon Acceleration",
                value=True,
                help=
                "Photon is Databricks' next-generation query engine that accelerates queries"
            )

            if st.form_submit_button("Add Transformation"):
                if transform_name:
                    if transform_name in [
                            t['name'] for t in st.session_state.conf_transforms
                    ]:
                        st.error(
                            "Transformation with this name already exists!")
                    else:
                        st.session_state.conf_transforms.append({
                            'name':
                            transform_name,
                            'service_tier':
                            service_tier,
                            'avg_duration':
                            avg_duration,
                            'runs_per_month':
                            runs_per_month,
                            'dbu_per_hour':
                            dbu_per_hour,
                            'storage_gb':
                            estimated_storage,
                            'photon_enabled':
                            enable_photon_transform
                        })
                        st.success(f"Transformation '{transform_name}' added!")
                else:
                    st.error("Please enter a transformation name")

        # Display added transformations
        if st.session_state.conf_transforms:
            st.subheader("Your CONF Layer Transformations")

            # Create DataFrame with costs calculation
            transform_data = []
            for transform in st.session_state.conf_transforms:
                # Map service tier to DBU type and cost
                dbu_type_map = {
                    "Databricks Jobs": "Jobs",
                    "Delta Live Tables (Core)": "DLT_Core",
                    "Delta Live Tables (Pro)": "DLT_Pro",
                    "Delta Live Tables (Advanced)": "DLT_Advanced"
                }
                dbu_type = dbu_type_map.get(transform['service_tier'], "Jobs")
                dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Jobs"])

                # Calculate hours for this transformation in a physical month
                monthly_hours = (transform['avg_duration'] /
                                 60) * transform['runs_per_month']

                # Calculate compute cost
                compute_cost = calculate_dbu_cost(
                    dbu_cost,
                    1,  # Cluster size (already factored into dbu_per_hour)
                    monthly_hours / 30,  # Hours per day
                    30,  # Days per physical month
                    transform['dbu_per_hour'])

                # Photon acceleration cost if enabled
                photon_cost = 0
                if transform['photon_enabled']:
                    photon_cost = calculate_photon_cost(
                        compute_cost, COSTS["Photon"]["acceleration_factor"])

                transform_data.append({
                    'Name':
                    transform['name'],
                    'Service Tier':
                    transform['service_tier'],
                    'Duration (min)':
                    transform['avg_duration'],
                    'Runs/Physical Month':
                    transform['runs_per_month'],
                    'DBUs/Hour':
                    transform['dbu_per_hour'],
                    'Storage (GB)':
                    transform['storage_gb'],
                    'Photon':
                    'Enabled' if transform['photon_enabled'] else 'Disabled',
                    'Compute Cost ($)':
                    round(compute_cost, 2),
                    'Photon Cost ($)':
                    round(photon_cost, 2)
                })

            df_transforms = pd.DataFrame(transform_data)
            st.dataframe(df_transforms)

            if st.button("Clear All Transformations"):
                st.session_state.conf_transforms = []
                st.rerun()

        # Storage tier selection
        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate costs for CONF layer (Advanced mode)
        if st.session_state.conf_transforms:
            # Compute, photon and storage costs
            total_compute_cost = 0
            total_photon_cost = 0
            total_storage_gb = 0

            for transform in st.session_state.conf_transforms:
                # Map service tier to DBU type and cost
                dbu_type_map = {
                    "Databricks Jobs": "Jobs",
                    "Delta Live Tables (Core)": "DLT_Core",
                    "Delta Live Tables (Pro)": "DLT_Pro",
                    "Delta Live Tables (Advanced)": "DLT_Advanced"
                }
                dbu_type = dbu_type_map.get(transform['service_tier'], "Jobs")
                dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Jobs"])

                # Calculate hours for this transformation in a physical month
                monthly_hours = (transform['avg_duration'] /
                                 60) * transform['runs_per_month']

                # Calculate compute cost
                compute_cost = calculate_dbu_cost(
                    dbu_cost,
                    1,  # Cluster size (already factored into dbu_per_hour)
                    monthly_hours / 30,  # Hours per day
                    30,  # Days per physical month
                    transform['dbu_per_hour'])

                # Add to total compute cost
                total_compute_cost += compute_cost

                # Photon acceleration cost if enabled
                if transform['photon_enabled']:
                    photon_cost = calculate_photon_cost(
                        compute_cost, COSTS["Photon"]["acceleration_factor"])
                    total_photon_cost += photon_cost

                # Accumulate storage
                total_storage_gb += transform['storage_gb']

            # Storage cost
            storage_cost = calculate_storage_cost(
                total_storage_gb,
                COSTS["S3"][storage_type],
                months=1  # For a single physical month
            )

            # Total cost
            total_cost = total_compute_cost + storage_cost + total_photon_cost

            # Store in session state
            st.session_state.all_costs["CONF"] = {
                "compute_cost":
                total_compute_cost,
                "storage_cost":
                storage_cost,
                "photon_cost":
                total_photon_cost,
                "total_cost":
                total_cost,
                "transforms_count":
                len(st.session_state.conf_transforms),
                "storage_gb":
                total_storage_gb,
                "photon_enabled":
                any(transform['photon_enabled']
                    for transform in st.session_state.conf_transforms)
            }

# PB LAYER CONFIGURATION
elif layer == "PB":
    st.subheader("PB Layer Configuration")

    # Add engine type selection
    engine_type = st.selectbox(
        "Engine Type", ["SQL", "PySpark", "Materialized View (MV)"],
        help="Select the type of engine for your data processing")

    mode = st.radio("Estimation Mode", ["Simple", "Advanced"],
                    horizontal=True,
                    key="pb_mode")

    # Different cost factors based on engine type
    engine_cost_factors = {
        "SQL": {
            "dbu_rate": COSTS["DBU"]["Enterprise"],
            "storage_multiplier": 1.0,
            "performance_factor": 1.0
        },
        "PySpark": {
            "dbu_rate": COSTS["DBU"]["Jobs"],
            "storage_multiplier":
            1.2,  # PySpark typically uses more storage due to intermediate results
            "performance_factor":
            1.5  # PySpark can be more powerful but uses more resources
        },
        "Materialized View (MV)": {
            "dbu_rate": COSTS["DBU"]["Enterprise"] *
            0.8,  # Materialized views are precomputed so query time is less
            "storage_multiplier":
            2.0,  # MV requires additional storage for the materialized data
            "performance_factor":
            0.5  # MV has lower compute needs for querying, but higher for refreshes
        }
    }

    # Get engine-specific cost factors
    engine_factors = engine_cost_factors[engine_type]

    if mode == "Simple":
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            num_dashboards = st.number_input(
                "Number of Dashboards",
                min_value=0,
                value=5,
                help="Total number of interactive dashboards")
            num_reports = st.number_input("Number of Reports",
                                          min_value=0,
                                          value=10,
                                          help="Total number of batch reports")

        with col2:
            active_users = st.number_input(
                "Number of Active Users",
                min_value=1,
                value=20,
                help="Users actively accessing dashboards")

            # Different size naming based on engine type
            if engine_type == "SQL":
                size_options = [
                    "Extra Small (1 DBU)", "Small (2 DBUs)", "Medium (4 DBUs)",
                    "Large (8 DBUs)"
                ]
                size_label = "SQL Warehouse Size"
            elif engine_type == "PySpark":
                size_options = [
                    "Small Cluster (2 DBUs)", "Medium Cluster (4 DBUs)",
                    "Large Cluster (8 DBUs)", "X-Large Cluster (16 DBUs)"
                ]
                size_label = "Cluster Size"
            else:  # Materialized View
                size_options = [
                    "Low Refresh (1 DBU)", "Medium Refresh (2 DBUs)",
                    "High Refresh (4 DBUs)", "Very High Refresh (8 DBUs)"
                ]
                size_label = "MV Refresh Size"

            compute_size = st.selectbox(
                size_label,
                size_options,
                index=1,  # Default to Small/Medium
                help=f"Size of compute resources for {engine_type}")

        col3, col4 = st.columns(2)
        with col3:
            avg_queries_per_day = st.number_input(
                "Average Queries per User per Day",
                min_value=1,
                value=15,
                help="How many queries each user runs daily")

            # Different duration label based on engine type
            if engine_type == "Materialized View (MV)":
                duration_label = "Average View Access Time (seconds)"
            else:
                duration_label = "Average Query Duration (seconds)"

            avg_query_duration = st.number_input(
                duration_label,
                min_value=1,
                value=8,
                help="Typical duration of queries or view access")

        with col4:
            if engine_type == "Materialized View (MV)":
                report_label = "MV Refresh Frequency per Physical Month"
                duration_label = "Average Refresh Duration (minutes)"
            else:
                report_label = "Report Runs per Physical Month"
                duration_label = "Average Report Duration (minutes)"

            report_runs_per_month = st.number_input(
                report_label,
                min_value=1,
                value=8,
                help=
                "How many times reports are run or views are refreshed monthly"
            )
            avg_report_duration = st.number_input(
                duration_label,
                min_value=1,
                value=45,
                help=
                "Typical duration for generating reports or refreshing views")

        # Photon is only available for SQL and partially for PySpark
        if engine_type != "Materialized View (MV)":
            enable_photon = st.checkbox(
                "Enable Photon Acceleration",
                value=True,
                help=
                "Photon is Databricks' next-generation query engine that accelerates queries"
            )
        else:
            enable_photon = False
            st.info(
                "Photon acceleration is not applicable for Materialized Views")

        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate costs for PB layer (Simple mode)
        # Map compute size to DBU based on engine type
        if engine_type == "SQL":
            size_map = {
                "Extra Small (1 DBU)": 1,
                "Small (2 DBUs)": 2,
                "Medium (4 DBUs)": 4,
                "Large (8 DBUs)": 8
            }
        elif engine_type == "PySpark":
            size_map = {
                "Small Cluster (2 DBUs)": 2,
                "Medium Cluster (4 DBUs)": 4,
                "Large Cluster (8 DBUs)": 8,
                "X-Large Cluster (16 DBUs)": 16
            }
        else:  # Materialized View
            size_map = {
                "Low Refresh (1 DBU)": 1,
                "Medium Refresh (2 DBUs)": 2,
                "High Refresh (4 DBUs)": 4,
                "Very High Refresh (8 DBUs)": 8
            }

        compute_dbu = size_map.get(compute_size, 2)

        # Dashboard/Interactive compute cost
        # Convert query duration from seconds to hours
        query_hours = (
            avg_query_duration /
            3600) * avg_queries_per_day * active_users * 22  # 22 working days

        # Apply engine-specific performance factor
        query_hours *= engine_factors["performance_factor"]

        dashboard_compute = calculate_dbu_cost(
            engine_factors["dbu_rate"],
            1,  # Cluster size (already factored into compute_dbu)
            query_hours / 22,  # Hours per day
            22,  # Working days per physical month
            compute_dbu)

        # Report/Batch compute cost
        report_hours = (avg_report_duration /
                        60) * report_runs_per_month * num_reports

        # For Materialized Views, use the same DBU rate but adjust hours based on refresh frequency
        report_compute = calculate_dbu_cost(
            engine_factors["dbu_rate"],
            1,  # Cluster size
            report_hours / 30,  # Hours per day
            30,  # Days per physical month
            compute_dbu  # Use the selected compute size
        )

        # Total compute cost
        compute_cost = dashboard_compute + report_compute

        # Photon acceleration cost if enabled (only for SQL and PySpark)
        photon_cost = 0
        if enable_photon:
            photon_cost = calculate_photon_cost(
                compute_cost, COSTS["Photon"]["acceleration_factor"])

        # Storage calculation with engine-specific multiplier
        dashboard_storage = num_dashboards * 20 * engine_factors[
            "storage_multiplier"]  # Approx 20GB per dashboard
        report_storage = num_reports * 50 * engine_factors[
            "storage_multiplier"]  # Approx 50GB per report
        total_storage_gb = dashboard_storage + report_storage

        storage_cost = calculate_storage_cost(
            total_storage_gb,
            COSTS["S3"][storage_type],
            months=1  # For a single physical month
        )

        # Total cost
        total_cost = compute_cost + storage_cost + photon_cost

        # Store in session state
        st.session_state.all_costs["PB"] = {
            "compute_cost": compute_cost,
            "storage_cost": storage_cost,
            "photon_cost": photon_cost,
            "total_cost": total_cost,
            "dashboards_count": num_dashboards,
            "reports_count": num_reports,
            "storage_gb": total_storage_gb,
            "photon_enabled": enable_photon,
            "engine_type": engine_type
        }

    else:  # Advanced mode
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)

        # Dashboard/Interactive Query configuration
        if engine_type == "Materialized View (MV)":
            st.subheader("Interactive MV Access")
        else:
            st.subheader("Interactive Dashboards")

        # Initialize session state for dashboards if not exists
        if 'pb_dashboards' not in st.session_state:
            st.session_state.pb_dashboards = []

        # Form to add new dashboards
        with st.form("add_dashboard_form"):
            col1, col2 = st.columns(2)
            with col1:
                if engine_type == "Materialized View (MV)":
                    dash_name = st.text_input(
                        "View Name",
                        help="Unique name for this materialized view")
                    size_label = "MV Access Tier"
                    size_options = [
                        "Low Usage (1 DBU)", "Medium Usage (2 DBUs)",
                        "High Usage (4 DBUs)", "Very High Usage (8 DBUs)"
                    ]
                elif engine_type == "PySpark":
                    dash_name = st.text_input(
                        "Dashboard Name",
                        help="Unique name for this dashboard")
                    size_label = "Cluster Size"
                    size_options = [
                        "Small Cluster (2 DBUs)", "Medium Cluster (4 DBUs)",
                        "Large Cluster (8 DBUs)", "X-Large Cluster (16 DBUs)"
                    ]
                else:  # SQL
                    dash_name = st.text_input(
                        "Dashboard Name",
                        help="Unique name for this dashboard")
                    size_label = "SQL Warehouse Size"
                    size_options = [
                        "Extra Small (1 DBU)", "Small (2 DBUs)",
                        "Medium (4 DBUs)", "Large (8 DBUs)"
                    ]

                compute_size = st.selectbox(
                    size_label,
                    size_options,
                    index=1,  # Default to Small/Medium
                    help=f"Compute resources for this {engine_type} dashboard")

            with col2:
                active_users = st.number_input(
                    "Active Users",
                    min_value=1,
                    value=10,
                    help="Users actively accessing this dashboard/view")
                queries_per_day = st.number_input(
                    "Queries per User per Day",
                    min_value=1,
                    value=10,
                    help="How many queries each user runs daily")

            if engine_type == "Materialized View (MV)":
                query_label = "Average View Access Time (seconds)"
            else:
                query_label = "Average Query Duration (seconds)"

            avg_query_duration = st.number_input(
                query_label,
                min_value=1,
                value=10,
                help="Typical duration of dashboard queries or view access")

            # Photon is only available for SQL and partially for PySpark
            if engine_type != "Materialized View (MV)":
                enable_photon_dash = st.checkbox(
                    "Enable Photon Acceleration",
                    value=True,
                    help=
                    "Photon is Databricks' next-generation query engine that accelerates queries"
                )
            else:
                enable_photon_dash = False

            if st.form_submit_button(
                    f"Add {'View' if engine_type == 'Materialized View (MV)' else 'Dashboard'}"
            ):
                if dash_name:
                    if dash_name in [
                            d['name'] for d in st.session_state.pb_dashboards
                    ]:
                        st.error(
                            f"{'View' if engine_type == 'Materialized View (MV)' else 'Dashboard'} with this name already exists!"
                        )
                    else:
                        st.session_state.pb_dashboards.append({
                            'name':
                            dash_name,
                            'compute_size':
                            compute_size,
                            'active_users':
                            active_users,
                            'queries_per_day':
                            queries_per_day,
                            'avg_query_duration':
                            avg_query_duration,
                            'photon_enabled':
                            enable_photon_dash,
                            'engine_type':
                            engine_type
                        })
                        st.success(
                            f"{'View' if engine_type == 'Materialized View (MV)' else 'Dashboard'} '{dash_name}' added!"
                        )
                else:
                    st.error(
                        f"Please enter a {'view' if engine_type == 'Materialized View (MV)' else 'dashboard'} name"
                    )

        # Display added dashboards
        if st.session_state.pb_dashboards:
            st.caption(
                f"Your {'Views' if engine_type == 'Materialized View (MV)' else 'Dashboards'}"
            )

            # Filter dashboards by current engine type
            current_engine_dashboards = [
                d for d in st.session_state.pb_dashboards
                if d.get('engine_type') == engine_type
            ]

            if current_engine_dashboards:
                # Create DataFrame with costs calculation
                dashboard_data = []
                for dash in current_engine_dashboards:
                    # Map compute size to DBU based on engine type
                    if dash['engine_type'] == "SQL":
                        size_map = {
                            "Extra Small (1 DBU)": 1,
                            "Small (2 DBUs)": 2,
                            "Medium (4 DBUs)": 4,
                            "Large (8 DBUs)": 8
                        }
                    elif dash['engine_type'] == "PySpark":
                        size_map = {
                            "Small Cluster (2 DBUs)": 2,
                            "Medium Cluster (4 DBUs)": 4,
                            "Large Cluster (8 DBUs)": 8,
                            "X-Large Cluster (16 DBUs)": 16
                        }
                    else:  # Materialized View
                        size_map = {
                            "Low Usage (1 DBU)": 1,
                            "Medium Usage (2 DBUs)": 2,
                            "High Usage (4 DBUs)": 4,
                            "Very High Usage (8 DBUs)": 8
                        }

                    compute_dbu = size_map.get(dash['compute_size'], 2)

                    # Apply engine-specific performance factor
                    engine_perf_factor = engine_cost_factors[
                        dash['engine_type']]["performance_factor"]

                    # Convert query duration from seconds to hours and apply performance factor
                    query_hours = (
                        dash['avg_query_duration'] /
                        3600) * dash['queries_per_day'] * dash[
                            'active_users'] * 22 * engine_perf_factor

                    # Use engine-specific DBU rate
                    engine_dbu_rate = engine_cost_factors[
                        dash['engine_type']]["dbu_rate"]

                    # Dashboard compute cost
                    compute_cost = calculate_dbu_cost(
                        engine_dbu_rate,
                        1,  # Cluster size (already factored into compute_dbu)
                        query_hours / 22,  # Hours per day
                        22,  # Working days per physical month
                        compute_dbu)

                    # Photon acceleration cost if enabled and applicable
                    photon_cost = 0
                    if dash['photon_enabled'] and dash[
                            'engine_type'] != "Materialized View (MV)":
                        photon_cost = calculate_photon_cost(
                            compute_cost,
                            COSTS["Photon"]["acceleration_factor"])

                    dashboard_data.append({
                        'Name':
                        dash['name'],
                        'Compute':
                        dash['compute_size'],
                        'Users':
                        dash['active_users'],
                        'Queries/Day':
                        dash['queries_per_day'],
                        'Duration (s)':
                        dash['avg_query_duration'],
                        'Photon':
                        'Enabled' if dash.get('photon_enabled', False)
                        and dash['engine_type'] != "Materialized View (MV)"
                        else 'Disabled',
                        'Monthly Cost ($)':
                        round(compute_cost + photon_cost, 2)
                    })

                df_dashboards = pd.DataFrame(dashboard_data)
                st.dataframe(df_dashboards)

                if st.button(
                        f"Clear All {engine_type} {'Views' if engine_type == 'Materialized View (MV)' else 'Dashboards'}",
                        key="clear_dashboards"):
                    # Only clear dashboards of the current engine type
                    st.session_state.pb_dashboards = [
                        d for d in st.session_state.pb_dashboards
                        if d.get('engine_type') != engine_type
                    ]
                    st.rerun()
            else:
                st.info(
                    f"No {engine_type} {'views' if engine_type == 'Materialized View (MV)' else 'dashboards'} added yet."
                )

        # Batch Reports/MV Refresh configuration
        if engine_type == "Materialized View (MV)":
            st.subheader("MV Refresh Jobs")
        else:
            st.subheader("Batch Reports")

        # Initialize session state for reports if not exists
        if 'pb_reports' not in st.session_state:
            st.session_state.pb_reports = []

        # Form to add new reports
        with st.form("add_report_form"):
            col1, col2 = st.columns(2)
            with col1:
                if engine_type == "Materialized View (MV)":
                    report_name = st.text_input(
                        "MV Refresh Job Name",
                        help="Unique name for this refresh job")
                    runs_label = "Refresh Frequency per Physical Month"
                else:
                    report_name = st.text_input(
                        "Report Name", help="Unique name for this report")
                    runs_label = "Runs per Physical Month"

                runs_per_month = st.number_input(
                    runs_label,
                    min_value=1,
                    value=4,
                    help=
                    f"How many times this {'view is refreshed' if engine_type == 'Materialized View (MV)' else 'report runs'} monthly"
                )

            with col2:
                if engine_type == "Materialized View (MV)":
                    duration_label = "Refresh Duration (min)"
                else:
                    duration_label = "Generation Duration (min)"

                gen_duration = st.number_input(
                    duration_label,
                    min_value=1,
                    value=30,
                    help=
                    f"Time taken to {'refresh the view' if engine_type == 'Materialized View (MV)' else 'generate this report'}"
                )

                # Different DBU label based on engine type
                if engine_type == "SQL":
                    dbu_label = "SQL Warehouse DBUs per Hour"
                elif engine_type == "PySpark":
                    dbu_label = "Cluster DBUs per Hour"
                else:
                    dbu_label = "Refresh DBUs per Hour"

                dbu_per_hour = st.number_input(
                    dbu_label,
                    min_value=1,
                    value=4 if engine_type == "PySpark" else 2,
                    help="Databricks Units consumed per hour")

            # Photon is not applicable for MV refreshes
            if engine_type != "Materialized View (MV)":
                enable_photon_report = st.checkbox(
                    "Enable Photon Acceleration",
                    value=True,
                    help=
                    "Photon is Databricks' next-generation query engine that accelerates queries"
                )
            else:
                enable_photon_report = False

            if st.form_submit_button(
                    f"Add {'Refresh Job' if engine_type == 'Materialized View (MV)' else 'Report'}"
            ):
                if report_name:
                    if report_name in [
                            r['name'] for r in st.session_state.pb_reports
                    ]:
                        st.error(
                            f"{'Refresh job' if engine_type == 'Materialized View (MV)' else 'Report'} with this name already exists!"
                        )
                    else:
                        st.session_state.pb_reports.append({
                            'name':
                            report_name,
                            'runs_per_month':
                            runs_per_month,
                            'gen_duration':
                            gen_duration,
                            'dbu_per_hour':
                            dbu_per_hour,
                            'photon_enabled':
                            enable_photon_report,
                            'engine_type':
                            engine_type
                        })
                        st.success(
                            f"{'Refresh job' if engine_type == 'Materialized View (MV)' else 'Report'} '{report_name}' added!"
                        )
                else:
                    st.error(
                        f"Please enter a {'refresh job' if engine_type == 'Materialized View (MV)' else 'report'} name"
                    )

        # Display added reports
        if st.session_state.pb_reports:
            st.caption(
                f"Your {'Refresh Jobs' if engine_type == 'Materialized View (MV)' else 'Reports'}"
            )

            # Filter reports by current engine type
            current_engine_reports = [
                r for r in st.session_state.pb_reports
                if r.get('engine_type') == engine_type
            ]

            if current_engine_reports:
                # Create DataFrame with costs calculation
                report_data = []
                for report in current_engine_reports:
                    # Convert duration to hours
                    report_hours = (report['gen_duration'] /
                                    60) * report['runs_per_month']

                    # Use engine-specific DBU rate
                    engine_dbu_rate = engine_cost_factors[
                        report['engine_type']]["dbu_rate"]

                    # Report compute cost
                    compute_cost = calculate_dbu_cost(
                        engine_dbu_rate,
                        1,  # Cluster size
                        report_hours / 30,  # Hours per day
                        30,  # Days per physical month
                        report['dbu_per_hour'])

                    # Photon acceleration cost if enabled and applicable
                    photon_cost = 0
                    if report['photon_enabled'] and report[
                            'engine_type'] != "Materialized View (MV)":
                        photon_cost = calculate_photon_cost(
                            compute_cost,
                            COSTS["Photon"]["acceleration_factor"])

                    report_data.append({
                        'Name':
                        report['name'],
                        'Runs/Physical Month':
                        report['runs_per_month'],
                        'Duration (min)':
                        report['gen_duration'],
                        'DBUs/Hour':
                        report['dbu_per_hour'],
                        'Photon':
                        'Enabled' if report.get('photon_enabled', False)
                        and report['engine_type'] != "Materialized View (MV)"
                        else 'Disabled',
                        'Monthly Cost ($)':
                        round(compute_cost + photon_cost, 2)
                    })

                df_reports = pd.DataFrame(report_data)
                st.dataframe(df_reports)

                if st.button(
                        f"Clear All {engine_type} {'Refresh Jobs' if engine_type == 'Materialized View (MV)' else 'Reports'}",
                        key="clear_reports"):
                    # Only clear reports of the current engine type
                    st.session_state.pb_reports = [
                        r for r in st.session_state.pb_reports
                        if r.get('engine_type') != engine_type
                    ]
                    st.rerun()
            else:
                st.info(
                    f"No {engine_type} {'refresh jobs' if engine_type == 'Materialized View (MV)' else 'reports'} added yet."
                )

        # Storage configuration
        st.subheader("PB Layer Storage")
        col1, col2 = st.columns(2)

        with col1:
            if engine_type == "Materialized View (MV)":
                storage_label = "Storage per View (GB)"
            else:
                storage_label = "Storage per Dashboard (GB)"

            dashboard_storage_per_dash = st.number_input(
                storage_label,
                min_value=1.0,
                value=20.0 * engine_factors["storage_multiplier"],
                help=
                f"Average storage space per {'view' if engine_type == 'Materialized View (MV)' else 'dashboard'}"
            )

        with col2:
            if engine_type == "Materialized View (MV)":
                storage_label = "Storage per Refresh Job (GB)"
            else:
                storage_label = "Storage per Report (GB)"

            report_storage_per_report = st.number_input(
                storage_label,
                min_value=1.0,
                value=50.0 * engine_factors["storage_multiplier"],
                help=
                f"Average storage space per {'refresh job' if engine_type == 'Materialized View (MV)' else 'report'}"
            )

        storage_type = st.selectbox(
            "Storage Tier",
            list(COSTS["S3"].keys()),
            help="Select the appropriate S3 storage tier")

        st.markdown('</div>', unsafe_allow_html=True)

        # Calculate costs for PB layer (Advanced mode)
        # Filter dashboards and reports by current engine type
        current_engine_dashboards = [
            d for d in st.session_state.pb_dashboards
            if d.get('engine_type') == engine_type
        ]
        current_engine_reports = [
            r for r in st.session_state.pb_reports
            if r.get('engine_type') == engine_type
        ]

        dashboard_count = len(current_engine_dashboards)
        report_count = len(current_engine_reports)

        if dashboard_count > 0 or report_count > 0:
            # Dashboard compute and photon costs
            total_dashboard_compute = 0
            total_dashboard_photon = 0

            for dash in current_engine_dashboards:
                # Map compute size to DBU based on engine type
                if dash['engine_type'] == "SQL":
                    size_map = {
                        "Extra Small (1 DBU)": 1,
                        "Small (2 DBUs)": 2,
                        "Medium (4 DBUs)": 4,
                        "Large (8 DBUs)": 8
                    }
                elif dash['engine_type'] == "PySpark":
                    size_map = {
                        "Small Cluster (2 DBUs)": 2,
                        "Medium Cluster (4 DBUs)": 4,
                        "Large Cluster (8 DBUs)": 8,
                        "X-Large Cluster (16 DBUs)": 16
                    }
                else:  # Materialized View
                    size_map = {
                        "Low Usage (1 DBU)": 1,
                        "Medium Usage (2 DBUs)": 2,
                        "High Usage (4 DBUs)": 4,
                        "Very High Usage (8 DBUs)": 8
                    }

                compute_dbu = size_map.get(dash['compute_size'], 2)

                # Apply engine-specific performance factor
                engine_perf_factor = engine_cost_factors[
                    dash['engine_type']]["performance_factor"]

                # Convert query duration from seconds to hours and apply performance factor
                query_hours = (dash['avg_query_duration'] /
                               3600) * dash['queries_per_day'] * dash[
                                   'active_users'] * 22 * engine_perf_factor

                # Use engine-specific DBU rate
                engine_dbu_rate = engine_cost_factors[
                    dash['engine_type']]["dbu_rate"]

                # Dashboard compute cost
                compute_cost = calculate_dbu_cost(
                    engine_dbu_rate,
                    1,  # Cluster size (already factored into compute_dbu)
                    query_hours / 22,  # Hours per day
                    22,  # Working days per physical month
                    compute_dbu)

                total_dashboard_compute += compute_cost

                # Photon acceleration cost if enabled and applicable
                if dash.get(
                        'photon_enabled', False
                ) and dash['engine_type'] != "Materialized View (MV)":
                    photon_cost = calculate_photon_cost(
                        compute_cost, COSTS["Photon"]["acceleration_factor"])
                    total_dashboard_photon += photon_cost

            # Report compute and photon costs
            total_report_compute = 0
            total_report_photon = 0

            for report in current_engine_reports:
                # Convert duration to hours
                report_hours = (report['gen_duration'] /
                                60) * report['runs_per_month']

                # Use engine-specific DBU rate
                engine_dbu_rate = engine_cost_factors[
                    report['engine_type']]["dbu_rate"]

                # Report compute cost
                compute_cost = calculate_dbu_cost(
                    engine_dbu_rate,
                    1,  # Cluster size
                    report_hours / 30,  # Hours per day
                    30,  # Days per physical month
                    report['dbu_per_hour'])

                total_report_compute += compute_cost

                # Photon acceleration cost if enabled and applicable
                if report.get(
                        'photon_enabled', False
                ) and report['engine_type'] != "Materialized View (MV)":
                    photon_cost = calculate_photon_cost(
                        compute_cost, COSTS["Photon"]["acceleration_factor"])
                    total_report_photon += photon_cost

            # Storage calculation
            dashboard_storage = dashboard_count * dashboard_storage_per_dash
            report_storage = report_count * report_storage_per_report
            total_storage_gb = dashboard_storage + report_storage

            storage_cost = calculate_storage_cost(
                total_storage_gb,
                COSTS["S3"][storage_type],
                months=1  # For a single physical month
            )

            # Total costs
            total_compute = total_dashboard_compute + total_report_compute
            total_photon = total_dashboard_photon + total_report_photon
            total_cost = total_compute + storage_cost + total_photon

            # Store in session state
            st.session_state.all_costs["PB"] = {
                "compute_cost":
                total_compute,
                "storage_cost":
                storage_cost,
                "photon_cost":
                total_photon,
                "total_cost":
                total_cost,
                "dashboards_count":
                dashboard_count,
                "reports_count":
                report_count,
                "storage_gb":
                total_storage_gb,
                "photon_enabled": (dashboard_count > 0 and any(
                    dash.get('photon_enabled', False)
                    for dash in current_engine_dashboards))
                or (report_count > 0 and any(
                    report.get('photon_enabled', False)
                    for report in current_engine_reports)),
                "engine_type":
                engine_type
            }

# COST SUMMARY
st.markdown("---")
st.header("Cost Summary")

# Total cost calculation
total_monthly_cost = 0
layers_with_costs = []

for layer_name, costs in st.session_state.all_costs.items():
    if costs and "total_cost" in costs:
        total_monthly_cost += costs["total_cost"]
        layers_with_costs.append(layer_name)
    elif costs and "storage_cost_per_month" in costs:
        total_monthly_cost += costs["storage_cost_per_month"]
        layers_with_costs.append(layer_name)

# Display summary by layer in table format
if layers_with_costs:
    st.subheader("Cost Breakdown by Layer")

    # Create a table for all layers
    cost_summary_data = []

    for layer_name in layers_with_costs:
        costs = st.session_state.all_costs[layer_name]

        # Different handling for Landing layer which only has storage
        if layer_name == "Landing" and "storage_cost_per_month" in costs:
            layer_summary = {
                "Layer":
                f"{layer_name}",
                "Storage Cost":
                f"${costs['storage_cost_per_month']:.2f}",
                "Compute Cost":
                "-",
                "Photon Cost":
                "-",
                "Total Cost":
                f"${costs['storage_cost_per_month']:.2f}",
                "Storage Size":
                f"{costs['storage_gb']:.1f} GB",
                "Resources":
                f"{costs.get('tables_count', '-')} Tables"
                if 'tables_count' in costs else "-"
            }
            cost_summary_data.append(layer_summary)

        # For other layers with compute, storage, and possibly photon costs
        elif "total_cost" in costs:
            resources = ""
            if "jobs_count" in costs:
                resources = f"{costs['jobs_count']} Jobs"
            elif "transforms_count" in costs:
                resources = f"{costs['transforms_count']} Transforms"
            elif "dashboards_count" in costs and "reports_count" in costs:
                resources = f"{costs['dashboards_count']} Dashboards / {costs['reports_count']} Reports"

            layer_summary = {
                "Layer":
                f"{layer_name}",
                "Storage Cost":
                f"${costs.get('storage_cost', 0):.2f}",
                "Compute Cost":
                f"${costs.get('compute_cost', 0):.2f}",
                "Photon Cost":
                f"${costs.get('photon_cost', 0):.2f}" if costs.get(
                    'photon_cost', 0) > 0 else "-",
                "Total Cost":
                f"${costs['total_cost']:.2f}",
                "Storage Size":
                f"{costs.get('storage_gb', 0):.1f} GB",
                "Resources":
                resources
            }
            cost_summary_data.append(layer_summary)

    # Add total row
    total_row = {
        "Layer": "TOTAL",
        "Storage Cost": "-",
        "Compute Cost": "-",
        "Photon Cost": "-",
        "Total Cost": f"${total_monthly_cost:.2f}",
        "Storage Size": "-",
        "Resources": "-"
    }
    cost_summary_data.append(total_row)

    # Create and display the DataFrame
    cost_summary_df = pd.DataFrame(cost_summary_data)
    st.markdown("""
    <style>
    .cost-table {
        font-size: 0.95rem;
    }
    .cost-table th {
        background-color: var(--primary-color);
        color: white;
        font-weight: bold;
        padding: 8px;
    }
    .cost-table td {
        padding: 8px;
    }
    .cost-table tr:last-child {
        font-weight: bold;
        background-color: #f0f0f0;
    }
    </style>
    """,
                unsafe_allow_html=True)

    # Display the DataFrame with a custom CSS class and highlight the last row (totals)
    st.dataframe(
        cost_summary_df,
        use_container_width=True,
        column_config={
            "Layer":
            st.column_config.TextColumn("Layer"),
            "Storage Cost":
            st.column_config.TextColumn("Storage Cost ($/physical mo)"),
            "Compute Cost":
            st.column_config.TextColumn("Compute Cost ($/physical mo)"),
            "Photon Cost":
            st.column_config.TextColumn("Photon Cost ($/physical mo)"),
            "Total Cost":
            st.column_config.TextColumn("Total Cost ($/physical mo)"),
            "Storage Size":
            st.column_config.TextColumn("Storage Size"),
            "Resources":
            st.column_config.TextColumn("Resources")
        },
        hide_index=True)

    # Total cost display
    st.subheader("Total Monthly Cost")
    st.markdown(f"""
        <div class="total-card">
            <h2 style="margin: 0; color: var(--primary-color);">${total_monthly_cost:.2f}</h2>
            <p style="margin: 5px 0 0 0; color: var(--secondary-color);">Estimated cost per physical month</p>
        </div>
    """,
                unsafe_allow_html=True)

    # Add photon explanation card if any layer uses photon
    photon_used = False
    for layer_name in layers_with_costs:
        costs = st.session_state.all_costs[layer_name]
        if "photon_enabled" in costs and costs["photon_enabled"]:
            photon_used = True
            break

    if photon_used:
        total_photon_cost = sum(
            costs.get("photon_cost", 0)
            for costs in st.session_state.all_costs.values()
            if isinstance(costs, dict))

        st.markdown(f"""
            <div class="photon-card">
                <h4 style="margin-top: 0;">Photon Acceleration Included</h4>
                <p>Photon is Databricks' next-generation query engine that provides 20% acceleration at a cost of ${total_photon_cost:.2f}/physical month</p>
            </div>
        """,
                    unsafe_allow_html=True)

    # Export options
    st.subheader("Export Options")

    if st.button("Generate Excel Report"):
        # Create a Pandas Excel writer with XlsxWriter
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        # Write each layer's data to a different worksheet
        for layer_name in layers_with_costs:
            costs = st.session_state.all_costs[layer_name]

            # Create a DataFrame for this layer
            if layer_name == "Landing":
                df = pd.DataFrame({
                    'Metric': [
                        'Storage Cost', 'Storage Size', 'Storage Tier',
                        'Retention Policy'
                    ],
                    'Value': [
                        f"${costs.get('storage_cost_per_month', 0):.2f}/physical month",
                        f"{costs.get('storage_gb', 0):.1f} GB",
                        costs.get('storage_tier', 'Standard'),
                        costs.get('retention_policy', '30 days')
                    ]
                })
            else:
                metrics = ['Total Cost', 'Compute Cost', 'Storage Cost']
                values = [
                    f"${costs.get('total_cost', 0):.2f}/physical month",
                    f"${costs.get('compute_cost', 0):.2f}/physical month",
                    f"${costs.get('storage_cost', 0):.2f}/physical month"
                ]

                if "photon_cost" in costs and costs["photon_cost"] > 0:
                    metrics.append('Photon Acceleration')
                    values.append(
                        f"${costs['photon_cost']:.2f}/physical month")

                metrics.append('Storage Size')
                values.append(f"{costs.get('storage_gb', 0):.1f} GB")

                # Add specific metrics based on layer
                if layer_name == "RAW" and "jobs_count" in costs:
                    metrics.append('Jobs Count')
                    values.append(str(costs['jobs_count']))
                elif layer_name == "CONF" and "transforms_count" in costs:
                    metrics.append('Transformations Count')
                    values.append(str(costs['transforms_count']))
                elif layer_name == "PB":
                    if "dashboards_count" in costs:
                        metrics.append('Dashboards Count')
                        values.append(str(costs['dashboards_count']))
                    if "reports_count" in costs:
                        metrics.append('Reports Count')
                        values.append(str(costs['reports_count']))

                df = pd.DataFrame({'Metric': metrics, 'Value': values})

            # Write the dataframe to an Excel sheet
            df.to_excel(writer, sheet_name=layer_name, index=False)

        # Add a summary sheet
        summary_data = {
            'Layer':
            layers_with_costs + ['TOTAL'],
            'Monthly Cost': [
                st.session_state.all_costs[layer].get(
                    'total_cost', st.session_state.all_costs[layer].get(
                        'storage_cost_per_month', 0))
                for layer in layers_with_costs
            ] + [total_monthly_cost]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Close the Pandas Excel writer and output the Excel file
        writer.close()
        excel_data = output.getvalue()

        # Create a download button
        st.download_button(
            label="Download Excel Report",
            data=excel_data,
            file_name="databricks_cost_estimate.xlsx",
            mime=
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Configure at least one layer to see the cost summary.")
