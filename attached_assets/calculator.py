"""
Cost calculation utilities for Databricks cloud calculator
"""

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
    }
}

# Default compute configuration
DEFAULT_COMPUTE = {
    "instance_type": "r5.xlarge",
    "num_instances": 2,
    "hours_per_day": 8,
    "days_per_month": 22
}

def calculate_landing_cost(params, storage_type):
    """
    Calculate the landing layer storage cost based on input parameters
    
    Args:
        params (dict): Input parameters for calculation
        storage_type (str): S3 storage tier type
        
    Returns:
        float: Monthly cost in USD
    """
    if "mode" in params and params["mode"] == "Advanced":
        # Calculate based on detailed table information
        total_gb = 0
        for table in params.get("tables", []):
            daily_gb = table["avg_file_size"] * table["files_per_day"]
            
            # Convert retention to days
            retention_map = {
                "30 days": 30,
                "60 days": 60,
                "90 days": 90,
                "180 days": 180,
                "1 year": 365,
                "2 years": 730,
                "Indefinite": 1095  # Assume 3 years for indefinite
            }
            retention_days = retention_map.get(table["retention"], 30)
            
            # Calculate total GB for this table
            table_gb = daily_gb * retention_days
            total_gb += table_gb
    else:
        # Simple mode calculation
        daily_gb = params.get("avg_file_size", 2.0) * params.get("files_per_day", 10)
        
        # Convert retention to days
        retention_map = {
            "30 days": 30,
            "60 days": 60,
            "90 days": 90,
            "180 days": 180,
            "1 year": 365,
            "2 years": 730,
            "Indefinite": 1095  # Assume 3 years for indefinite
        }
        retention_days = retention_map.get(params.get("retention", "30 days"), 30)
        
        # Calculate storage needed for all tables
        total_gb = daily_gb * retention_days * params.get("num_tables", 5)
    
    # Apply growth factor if provided
    if "file_growth" in params:
        growth_factor = 1 + (params["file_growth"] / 100)
        total_gb = total_gb * growth_factor
    
    # Calculate cost based on storage type
    cost_per_gb = COSTS["S3"].get(storage_type, COSTS["S3"]["Standard"])
    monthly_cost = total_gb * cost_per_gb
    
    return monthly_cost

def calculate_raw_cost(params, storage_type):
    """
    Calculate the RAW layer computation and storage cost
    
    Args:
        params (dict): Input parameters for calculation
        storage_type (str): S3 storage tier type
        
    Returns:
        dict: Compute and storage costs
    """
    if "mode" in params and params["mode"] == "Advanced":
        # Calculate based on detailed job information
        compute_cost = 0
        for job in params.get("jobs", []):
            instance_cost = COSTS["EC2"].get(job["instance_type"], COSTS["EC2"]["r5.xlarge"])
            hours_per_run = job["avg_duration"] / 60  # Convert minutes to hours
            monthly_hours = hours_per_run * job["runs_per_month"]
            job_cost = instance_cost * monthly_hours
            compute_cost += job_cost
            
        # Estimate storage based on number of jobs
        storage_gb = len(params.get("jobs", [])) * 100  # Rough estimate
    else:
        # Simple mode calculation
        num_jobs = params.get("num_jobs", 3)
        avg_runs = params.get("avg_runs_per_month", 30)
        avg_duration = params.get("avg_job_duration", 45) / 60  # Convert to hours
        
        # Select instance type based on family
        instance_family_map = {
            "General Purpose (r5)": "r5.xlarge",
            "Memory Optimized (r5)": "r5.4xlarge",
            "Compute Optimized (i3)": "i3.2xlarge"
        }
        instance_type = instance_family_map.get(
            params.get("instance_family", "General Purpose (r5)"), 
            "r5.xlarge"
        )
        
        instance_cost = COSTS["EC2"].get(instance_type, COSTS["EC2"]["r5.xlarge"])
        compute_cost = num_jobs * avg_runs * avg_duration * instance_cost
        
        # Estimate storage based on number of tables
        storage_gb = params.get("num_tables", 10) * 50  # Rough estimate
    
    # Calculate storage cost
    cost_per_gb = COSTS["S3"].get(storage_type, COSTS["S3"]["Standard"])
    storage_cost = storage_gb * cost_per_gb
    
    return {
        "compute": compute_cost,
        "storage": storage_cost,
        "total": compute_cost + storage_cost
    }

def calculate_conf_cost(params, storage_type):
    """
    Calculate the CONF layer costs
    
    Args:
        params (dict): Input parameters for calculation
        storage_type (str): S3 storage tier type
        
    Returns:
        dict: Cost breakdown
    """
    if "mode" in params and params["mode"] == "Advanced":
        # Calculate based on detailed transformation information
        compute_cost = 0
        for transform in params.get("transforms", []):
            # Calculate DBU cost
            dbu_type = transform.get("dbu_type", "Jobs")
            dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Jobs"])
            dbu_per_hour = transform.get("dbu_per_hour", 4)
            hours_per_run = transform.get("avg_duration", 60) / 60  # Convert minutes to hours
            monthly_hours = hours_per_run * transform.get("runs_per_month", 30)
            transform_cost = dbu_cost * dbu_per_hour * monthly_hours
            compute_cost += transform_cost
            
        # Estimate storage based on number of transformations
        storage_gb = len(params.get("transforms", [])) * 80  # Rough estimate
    else:
        # Simple mode calculation
        num_transforms = params.get("num_transforms", 4)
        avg_runs = params.get("avg_runs_per_month", 30)
        avg_duration = params.get("avg_transform_duration", 60) / 60  # Convert to hours
        dbu_per_hour = params.get("dbu_per_hour", 4)
        
        # Select DBU type based on service tier
        dbu_type_map = {
            "Databricks Jobs": "Jobs",
            "Delta Live Tables (Core)": "DLT_Core",
            "Delta Live Tables (Pro)": "DLT_Pro",
            "Delta Live Tables (Advanced)": "DLT_Advanced"
        }
        dbu_type = dbu_type_map.get(
            params.get("service_tier", "Databricks Jobs"), 
            "Jobs"
        )
        
        dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Jobs"])
        compute_cost = num_transforms * avg_runs * avg_duration * dbu_per_hour * dbu_cost
        
        # Estimate storage based on number of transformations and complexity
        complexity_factor = {
            "Low": 0.7,
            "Medium": 1.0,
            "High": 1.5
        }.get(params.get("transform_complexity", "Medium"), 1.0)
        
        storage_gb = params.get("num_transforms", 4) * 50 * complexity_factor  # Rough estimate
    
    # Calculate storage cost
    cost_per_gb = COSTS["S3"].get(storage_type, COSTS["S3"]["Standard"])
    storage_cost = storage_gb * cost_per_gb
    
    return {
        "compute": compute_cost,
        "storage": storage_cost,
        "total": compute_cost + storage_cost
    }

def calculate_pb_cost(params, storage_type):
    """
    Calculate the PB layer costs
    
    Args:
        params (dict): Input parameters for calculation
        storage_type (str): S3 storage tier type
        
    Returns:
        dict: Cost breakdown
    """
    if "mode" in params and params["mode"] == "Advanced":
        # Calculate based on detailed dashboard/report information
        compute_cost = 0
        
        # Process interactive dashboards
        for dashboard in params.get("dashboards", []):
            # Calculate query cost based on DBU
            dbu_type = "Enterprise"  # SQL warehouses use Enterprise DBUs
            dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Enterprise"])
            dbu_per_hour = dashboard.get("warehouse_size", 2) * 1.5  # Small=2, Medium=4, Large=8, etc.
            
            # Calculate hours based on users and usage patterns
            active_users = dashboard.get("active_users", 10)
            queries_per_user = dashboard.get("queries_per_day", 10)
            avg_query_duration = dashboard.get("avg_query_duration", 10) / 3600  # Convert seconds to hours
            
            # Assume working days in a month (22)
            monthly_hours = active_users * queries_per_user * avg_query_duration * 22
            dashboard_cost = dbu_cost * dbu_per_hour * monthly_hours
            compute_cost += dashboard_cost
            
        # Process batch reports
        for report in params.get("reports", []):
            # Calculate report generation cost
            dbu_type = "Jobs"  # Batch reports use Jobs pricing
            dbu_cost = COSTS["DBU"].get(dbu_type, COSTS["DBU"]["Jobs"])
            dbu_per_hour = report.get("dbu_per_hour", 2)
            
            hours_per_run = report.get("gen_duration", 30) / 60  # Convert minutes to hours
            runs_per_month = report.get("runs_per_month", 4)
            
            report_cost = dbu_cost * dbu_per_hour * hours_per_run * runs_per_month
            compute_cost += report_cost
            
        # Estimate storage based on number of dashboards and reports
        dashboard_storage = len(params.get("dashboards", [])) * 20  # Approx 20GB per dashboard
        report_storage = len(params.get("reports", [])) * 50  # Approx 50GB per report
        storage_gb = dashboard_storage + report_storage
    else:
        # Simple mode calculation
        num_dashboards = params.get("num_dashboards", 5)
        num_reports = params.get("num_reports", 10)
        active_users = params.get("active_users", 20)
        
        # Warehouse size selection
        warehouse_size_map = {
            "Extra Small (1 DBU)": 1,
            "Small (2 DBUs)": 2,
            "Medium (4 DBUs)": 4,
            "Large (8 DBUs)": 8
        }
        warehouse_size = warehouse_size_map.get(
            params.get("warehouse_size", "Small (2 DBUs)"), 
            2
        )
        
        # Calculate dashboard usage
        avg_queries_per_day = params.get("avg_queries_per_day", 15)
        avg_query_duration = params.get("avg_query_duration", 8) / 3600  # Convert seconds to hours
        
        # Dashboard compute cost (Enterprise DBU pricing for SQL warehouses)
        dbu_cost = COSTS["DBU"]["Enterprise"]
        dashboard_hours = active_users * avg_queries_per_day * avg_query_duration * 22  # 22 working days
        dashboard_compute = dbu_cost * warehouse_size * dashboard_hours
        
        # Report compute cost (Jobs pricing for batch reports)
        report_runs = params.get("report_runs_per_month", 8)
        avg_report_duration = params.get("avg_report_duration", 45) / 60  # Convert minutes to hours
        report_dbu_per_hour = 2  # Default for reports
        
        report_compute = COSTS["DBU"]["Jobs"] * report_dbu_per_hour * report_runs * avg_report_duration * num_reports
        
        # Total compute cost
        compute_cost = dashboard_compute + report_compute
        
        # Storage calculation
        dashboard_storage = num_dashboards * 20  # Approx 20GB per dashboard
        report_storage = num_reports * 50  # Approx 50GB per report
        storage_gb = dashboard_storage + report_storage
    
    # Calculate storage cost
    cost_per_gb = COSTS["S3"].get(storage_type, COSTS["S3"]["Standard"])
    storage_cost = storage_gb * cost_per_gb
    
    return {
        "compute": compute_cost,
        "storage": storage_cost,
        "total": compute_cost + storage_cost
    }
