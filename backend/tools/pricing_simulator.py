"""
Simulated freight pricing API.
Returns realistic cost breakdowns for shipments based on mode, weight,
distance, and carrier. Designed to be swappable with a real pricing API.
"""

import json
import os
import random
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

_carriers_cache: Optional[Dict] = None


def _load_carriers() -> Dict:
    global _carriers_cache
    if _carriers_cache is None:
        with open(os.path.join(DATA_DIR, "carriers.json"), "r") as f:
            _carriers_cache = json.load(f)
    return _carriers_cache


def _demand_multiplier() -> float:
    """Simulate seasonal demand variation (1.0 = normal, up to 1.4 = peak)."""
    # Deterministic but varied based on a simple hash for consistency
    return random.uniform(0.9, 1.3)


def calculate_freight_cost(
    mode: str,
    weight_kg: float,
    distance_km: float,
    carrier_id: Optional[str] = None
) -> Dict:
    """
    Calculate freight cost for a shipment.

    Returns:
        Dict with freight, fuel_surcharge, customs, insurance, handling, total
    """
    carriers = _load_carriers()
    mode_carriers = carriers.get(mode, carriers.get("sea", []))

    # Pick carrier
    carrier = None
    if carrier_id:
        for c in mode_carriers:
            if c["id"] == carrier_id:
                carrier = c
                break
    if carrier is None:
        carrier = mode_carriers[0] if mode_carriers else {
            "base_rate_per_kg": 1.0,
            "fuel_surcharge_pct": 0.15,
            "min_charge_usd": 200,
            "name": "Generic Carrier",
            "id": "generic"
        }

    # Base freight cost
    demand = _demand_multiplier()
    base_rate = carrier["base_rate_per_kg"] * demand

    # Distance factor (longer routes have slight per-km discount)
    if distance_km > 10000:
        distance_factor = 0.85
    elif distance_km > 5000:
        distance_factor = 0.92
    else:
        distance_factor = 1.0

    freight = max(
        weight_kg * base_rate * distance_factor,
        carrier.get("min_charge_usd", 200)
    )

    # Fuel surcharge
    fuel_surcharge = freight * carrier["fuel_surcharge_pct"]

    # Customs and documentation fees
    customs_base = {"air": 120, "sea": 180, "road": 80}
    customs = customs_base.get(mode, 100) + (weight_kg * 0.02)

    # Insurance (0.3% - 0.5% of estimated cargo value, estimated from weight)
    estimated_value = weight_kg * 15  # rough avg cargo value per kg
    insurance = estimated_value * random.uniform(0.003, 0.005)

    # Handling fees
    handling = {"air": 85, "sea": 150, "road": 60}
    handling_fee = handling.get(mode, 80)

    total = freight + fuel_surcharge + customs + insurance + handling_fee

    return {
        "carrier_id": carrier["id"],
        "carrier_name": carrier.get("name", carrier["id"]),
        "mode": mode,
        "freight": round(freight, 2),
        "fuel_surcharge": round(fuel_surcharge, 2),
        "customs_and_docs": round(customs, 2),
        "insurance": round(insurance, 2),
        "handling": round(handling_fee, 2),
        "total": round(total, 2),
        "currency": "USD",
        "rate_per_kg": round(base_rate, 2),
        "demand_factor": round(demand, 2)
    }


def get_all_carrier_quotes(
    mode: str,
    weight_kg: float,
    distance_km: float
) -> List[Dict]:
    """Get pricing from all carriers for a given mode."""
    carriers = _load_carriers()
    mode_carriers = carriers.get(mode, [])

    quotes = []
    for carrier in mode_carriers:
        quote = calculate_freight_cost(mode, weight_kg, distance_km, carrier["id"])
        quotes.append(quote)

    return sorted(quotes, key=lambda x: x["total"])


def get_best_price(mode: str, weight_kg: float, distance_km: float) -> Dict:
    """Get the cheapest carrier quote for a given mode."""
    quotes = get_all_carrier_quotes(mode, weight_kg, distance_km)
    return quotes[0] if quotes else calculate_freight_cost(mode, weight_kg, distance_km)
