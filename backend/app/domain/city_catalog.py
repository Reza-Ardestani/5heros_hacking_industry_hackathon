"""Public City dataset identifiers and attribution; no IO."""

BASE = "https://data.calgary.ca/resource/{}.json?"
LICENSE = {
    "license_url": "https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa",
    "attribution": "Contains information licensed under the Open Government Licence – City of Calgary",
}
DISCOVERED_FROM = "https://www.calgary.ca/roads/conditions/traffic-cameras.html"
DATASETS = {
    "incidents": ("35ra-9556", "Traffic Incidents (unofficial archive)"),
    "current_incidents": ("4jah-h97u", "Current Traffic Incidents"),
    "closures": ("w8zq-79bq", "Construction Detours (scheduled road/lane closures)"),
    "projects": ("sizs-hgef", "Road Construction Projects"),
    "cameras": ("k7p9-kppz", "Traffic Cameras"),
    "signals": ("qr97-4jvx", "Traffic Signals"),
    "travel_times": ("aeb8-fh2w", "Travel Times"),
    "volumes_2024": ("cauu-7hnw", "Traffic Volumes for 2024"),
}
