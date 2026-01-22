CANONICAL = {
    # --- Temperature / humidity / derived microclimate ---
    "temperature": [
        "air temperature",
        "HC Air temperature",
        "Drybulb temperature, high precision",
        "drybulb temperature",
        "microclimate temperature",
        "microclimate_temperature",
        "air_temperature",
        "temperature celsius",
        "ambient temperature",
    ],
    "relative humidity": [
        "relative humidity",
        "HC Relative humidity",
        "microclimate relative humidity",
        "microclimate_relative_humidity",
        "relative_humidity",
        "humidity percent",
        "RH",
    ],
    "dew point": [
        "dew point",
        "Dew Point",
        "microclimate dew point",
        "microclimate_dew_point",
        "dew_point",
    ],
    "delta t": [
        "DeltaT",
        "delta t",
        "temperature delta",
        "DeltaT avg",
        "DeltaT min",
        "DeltaT max",
    ],
    "vpd": [
        "VPD",
        "vapor pressure deficit",
        "vapour pressure deficit",
        "VPD avg",
        "VPD min",
    ],
    "microclimate absolute humidity": [
        "microclimate absolute humidity",
        "microclimate_absolute_humidity",
        "absolute humidity",
    ],

    # --- Radiation / solar ---
    "solar radiation": [
        "solar radiation",
        "Solar radiation",
        "KZ Solar radiation",
        "solar_radiation",
        "global radiation",
        "irradiance",
        "shortwave radiation",
    ],

    # --- Wind ---
    "wind speed": [
        "wind speed",
        "U-sonic wind speed",
        "wind_speed",
        "U-sonic wind speed avg",
        "U-sonic wind speed max",
        "anemometer wind speed",
    ],
    "wind direction": [
        "wind direction",
        "U-sonic wind dir",
        "wind_direction",
        "wind dir",
        "wind bearing",
    ],
    "wind gust": [
        "wind gust",
        "Wind gust",
        "gust speed",
        "Wind gust max",
    ],

    # --- Pressure ---
    "atmospheric pressure": [
        "atmospheric pressure",
        "air pressure",
        "barometric pressure",
        "atmospheric_pressure",
    ],

    # --- Rain / precipitation ---
    "precipitation": [
        "precipitation",
        "Precipitation",
        "daily rainfall",
        "daily_rainfall",
        "total rainfall",
        "total_rainfall",
        "rain",
        "rainfall",
        "Precipitation sum",
    ],
    "rain intensity": [
        "rain intensity",
        "rain_intensity",
        "rain rate",
        "precipitation intensity",
    ],

    # --- Evapotranspiration ---
    "evapotranspiration": [
        "evapotranspiration",
        "hourly evapotranspiration",
        "hourly_evapotranspiration",
        "ET",
        "ET0",
    ],

    # --- Leaf wetness ---
    "leaf wetness": [
        "Leaf Wetness",
        "leaf wetness",
        "leaf wetness time",
        "microclimate upper leaf wetness",
        "microclimate_upper_leaf_wetness",
        "microclimate lower leaf wetness",
        "microclimate_lower_leaf_wetness",
    ],

    # --- Soil temperature ---
    "soil temperature": [
        "Soil temperature",
        "soil temperature",
        "Soil temperature 3",
        "Soil temperature 4",
        "Soil temperature 5",
        "Soil temperature 6",
        "Soil temperature 7",
        "Soil temperature 8",
        "Soil temperature 9",
        "Soil temperature 10",
        "Soil temperature 11",
        "Soil temperature 12",
        "soil temp at depth",
    ],

    # --- Soil moisture (volumetric water content) ---
    "soil moisture": [
        "soil moisture",
        "Aqua Soil Moisture",
        "Aqua Soil Moisture 3",
        "Aqua Soil Moisture 4",
        "Aqua Soil Moisture 5",
        "Aqua Soil Moisture 6",
        "EAG Soil moisture",
        "EAG Soil moisture 3",
        "EAG Soil moisture 4",
        "EAG Soil moisture 5",
        "EAG Soil moisture 6",
        "EAG Soil moisture 7",
        "EAG Soil moisture 8",
        "EAG Soil moisture 9",
        "EAG Soil moisture 10",
        "EAG Soil moisture 11",
        "EAG Soil moisture 12",
        "volumetric water content",
        "VWC",
    ],

    # --- Soil salinity / conductivity / ionic ---
    "volumetric ionic content": [
        "Volumetric Ionic Content",
        "Volumetric Ionic Content 3",
        "Volumetric Ionic Content 4",
        "Volumetric Ionic Content 5",
        "Volumetric Ionic Content 6",
        "Volumetric Ionic Content 7",
        "Volumetric Ionic Content 8",
        "Volumetric Ionic Content 9",
        "Volumetric Ionic Content 10",
        "Volumetric Ionic Content 11",
        "Volumetric Ionic Content 12",
        "ionic content",
        "salinity",
        "conductivity",
        "EC",
    ],

    # --- Power / voltages ---
    "battery": [
        "battery voltage",
        "Battery",
        "battery_voltage",
        "Battery last",
    ],
    "panel": [
        "solar panel voltage",
        "Solar Panel",
        "panel voltage",
        "pv voltage",
        "Solar Panel last",
    ],
    "supply": [
        "supply voltage",
        "system voltage",
        "supply_voltage",
    ],

    # --- Water meter / irrigation ---
    "water meter increment": [
        "water meter increment",
        "Water meter 0.1L - Increment",
        "water meter 0.1L increment",
        "pulse counter",
        "flow meter pulse",
    ],
}


CANONICAL_META = {
    # --- Temperature / humidity / derived microclimate ---
    "temperature": {
        "units": ["°C", "C", "degC"],
        "aggregations": ["avg", "min", "max", "last"],
    },
    "relative humidity": {
        "units": ["%", "percent"],
        "aggregations": ["avg", "min", "max", "last"],
    },
    "dew point": {
        "units": ["°C", "C", "degC"],
        "aggregations": ["avg", "min", "max", "last"],
    },
    "delta t": {
        "units": ["°C", "C", "degC"],
        "aggregations": ["avg", "min", "max", "last"],
    },
    "vpd": {
        "units": ["kPa", "hPa", "Pa"],
        "aggregations": ["avg", "min", "max", "last"],
    },
    "microclimate absolute humidity": {
        "units": ["g/m3", "g/m³", "kg/m3", "kg/m³"],
        "aggregations": ["avg", "min", "max", "last"],
    },

    # --- Radiation / solar ---
    "solar radiation": {
        "units": ["W/m2", "W/m²"],
        "aggregations": ["avg", "min", "max", "last"],
    },

    # --- Wind ---
    "wind speed": {
        "units": ["m/s", "km/h", "mph"],
        "aggregations": ["avg", "max", "min", "last"],  # you have avg/max; keep min/last possible
    },
    "wind direction": {
        "units": ["°", "deg", "degrees"],
        "aggregations": ["last", "avg"],  # you have last; avg can exist depending on vendor
    },
    "wind gust": {
        "units": ["m/s", "km/h", "mph"],
        "aggregations": ["max", "last"],
    },

    # --- Pressure ---
    "atmospheric pressure": {
        "units": ["hPa", "mbar", "kPa", "Pa"],
        "aggregations": ["avg", "min", "max", "last"],
    },

    # --- Rain / precipitation ---
    "precipitation": {
        "units": ["mm", "L/m2", "L/m²"],
        "aggregations": ["sum", "last"],  # you have sum; last sometimes exists as running total
    },
    "rain intensity": {
        "units": ["mm/h", "mm/hr", "mmh", "in/h"],
        "aggregations": ["avg", "max", "last"],
    },

    # --- Evapotranspiration ---
    "evapotranspiration": {
        "units": ["mm", "mm/day", "mm/d", "mm/h"],
        "aggregations": ["sum", "avg", "last"],  # depends on your ET series; daily/hourly often treated as sum
    },

    # --- Leaf wetness ---
    "leaf wetness": {
        "units": ["%", "percent", "s", "sec", "minutes", "hours"],
        "aggregations": ["time", "avg", "last"],  # you explicitly have "time"
    },

    # --- Soil temperature ---
    "soil temperature": {
        "units": ["°C", "C", "degC"],
        "aggregations": ["avg", "min", "max", "last"],
    },

    # --- Soil moisture (volumetric water content) ---
    "soil moisture": {
        "units": ["%", "percent", "m3/m3", "m³/m³"],
        "aggregations": ["avg", "min", "max", "last"],
    },

    # --- Soil salinity / conductivity / ionic ---
    "volumetric ionic content": {
        "units": ["dS/m", "mS/cm", "uS/cm", "µS/cm"],
        "aggregations": ["avg", "min", "max", "last"],
    },

    # --- Power / voltages ---
    "battery": {
        "units": ["V", "mV"],
        "aggregations": ["last", "avg", "min", "max"],
    },
    "panel": {
        "units": ["V", "mV"],
        "aggregations": ["last", "avg", "min", "max"],
    },
    "supply": {
        "units": ["V", "mV"],
        "aggregations": ["last", "avg", "min", "max"],
    },

    # --- Water meter / irrigation ---
    "water meter increment": {
        "units": ["L", "liters", "m3", "m³", "pulses", "count"],
        "aggregations": ["last", "sum", "increment"],
    },
}
