"""
Cost formula utilities for Databricks Cloud Cost Calculator
"""

def calculate_storage_cost(storage_size, storage_tier_cost, months=1):
    """Calculate storage cost based on size and tier cost"""
    return storage_size * storage_tier_cost * months

def calculate_compute_cost(instance_cost, num_instances, hours_per_day, days_per_month):
    """Calculate compute cost based on instance details"""
    return instance_cost * num_instances * hours_per_day * days_per_month

def calculate_dbu_cost(dbu_rate, cluster_size, hours_per_day, days_per_month, dbu_per_hour=1):
    """Calculate DBU cost based on usage"""
    return dbu_rate * cluster_size * hours_per_day * days_per_month * dbu_per_hour

def calculate_photon_cost(base_compute_cost, photon_acceleration_factor=0.2):
    """
    Calculate Photon cost as a percentage of base compute cost
    Default acceleration factor is 20% (0.2) of the base compute cost
    """
    return base_compute_cost * photon_acceleration_factor