import math

def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance in km"""
    if None in (lat1, lon1, lat2, lon2):
        return None

    R = 6371.0  # Earth radius km
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def delivery_fee_from_km(km):
    """Fee tiers"""
    if km is None:
        return 25.0  # default
    if km <= 3:
        return 25.0
    if km <= 5:
        return 45.0
    return 70.0