import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Initialize geocoder
geolocator = Nominatim(user_agent="pharmacy_gps_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Sample data (first 5 entries from your document)
sample_data = [
    {"Name": "PHIE PLANTIER", "Address": "2310 AVENUE MARECHAL JUIN", "Postal Code": "06250", "City": "MOUGINS", "Type": "T2"},
    {"Name": "PHIE SAINT MARTINS SELAS", "Address": "1009 AV ST MARTIN", "Postal Code": "06250", "City": "MOUGINS", "Type": "T3"},
    {"Name": "PHIE CHANAY ET LAUZE SELARL", "Address": "21 RUE FELIX FAURE", "Postal Code": "06400", "City": "CANNES", "Type": "T2"},
    {"Name": "CARREFOUR NICE FRA076", "Address": "RN 202 ROUTE DE DIGNE", "Postal Code": "06200", "City": "NICE", "Type": "PARA ENSEIGNE"},
    {"Name": "PHIE DU MARCHE SELARL", "Address": "11 RUE DOCTEUR BALOUX", "Postal Code": "06150", "City": "CANNES", "Type": "T1"},
]

# Function to get GPS coordinates with caching
@st.cache_data
def get_gps_coordinates(df):
    def geocode_address(row):
        full_address = f"{row['Address']}, {row['Postal Code']} {row['City']}, France"
        try:
            location = geocode(full_address)
            if location:
                return pd.Series([location.latitude, location.longitude])
            return pd.Series([None, None])
        except Exception as e:
            st.warning(f"Error geocoding {full_address}: {e}")
            return pd.Series([None, None])

    df[['Latitude', 'Longitude']] = df.apply(geocode_address, axis=1)
    return df

# Streamlit app
st.title("Pharmacy GPS Locator")

# Sidebar for data source selection
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Choose data source:", ("Sample Data", "Upload CSV"))

if data_source == "Sample Data":
    df = pd.DataFrame(sample_data)
else:
    uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Data Preview:")
        st.dataframe(df.head())
    else:
        st.warning("Please upload a CSV file to proceed.")
        df = pd.DataFrame()  # Empty DataFrame if no file is uploaded

# Process data if available
if not df.empty:
    st.header("Processing Addresses")
    with st.spinner("Geocoding addresses... This may take a moment."):
        df_with_gps = get_gps_coordinates(df)

    # Display the table
    st.subheader("Pharmacy Locations")
    st.dataframe(df_with_gps)

    # Filter out rows with missing coordinates for the map
    map_data = df_with_gps.dropna(subset=['Latitude', 'Longitude'])[['Latitude', 'Longitude']]

    if not map_data.empty:
        st.subheader("Map View")
        st.map(map_data)
    else:
        st.warning("No valid GPS coordinates available for mapping.")

    # Download option
    csv = df_with_gps.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name="pharmacy_gps_locations.csv",
        mime="text/csv",
    )
else:
    st.info("Please select a data source to begin.")

# Instructions
st.sidebar.markdown("""
### Instructions
1. Choose "Sample Data" to see a demo with 5 entries.
2. Or upload a CSV file with columns: `Name`, `Address`, `Postal Code`, `City`, `Type`.
3. Wait for geocoding to complete (may take time for large datasets).
4. View the table and map, then download the results.
""")
