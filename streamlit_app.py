import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt

# Ρύθμιση για αυτόματη ανανέωση κάθε 30 δευτερόλεπτα
st_autorefresh(interval=30000, key="datarefresh")

# Φορτώστε τις εικόνες τοπικά στο project
sunny_image_path = "sun.webp"
rainy_image_path = "rain.webp"

# Συνάρτηση για την ανάκτηση δεδομένων από τα API
def fetch_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"Error fetching data from {url}. Status code: {response.status_code}")
        return None
    try:
        data = response.json()
        return data
    except ValueError:
        st.error("Error decoding JSON response.")
        return None

# Διευθύνσεις API
url_sensor1 = "https://stayrostsamadias.pythonanywhere.com/api/data"
url_sensor2 = "https://saek2025.pythonanywhere.com/data"
url_computer_data = "https://stayrostsamadias.pythonanywhere.com/data"
url_mistral = "https://stayrostsamadias.pythonanywhere.com/api/data3"

# Ανάκτηση δεδομένων από τα API
data_sensor1 = fetch_data(url_sensor1)
data_sensor2 = fetch_data(url_sensor2)
data_computer = fetch_data(url_computer_data)
data_mistral = fetch_data(url_mistral)

# Μετατροπή των δεδομένων του αισθητήρα 2 σε DataFrame
df_sensor2 = pd.DataFrame([data_sensor2])

# Έλεγχος και μετατροπή δεδομένων σε DataFrame
def to_dataframe(data, index_label="index"):
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        raise ValueError("Unsupported data format")

    if df.empty:
        st.warning(f"No data available for {index_label}")
    else:
        df.index.name = index_label
    return df

df_sensor1 = to_dataframe(data_sensor1, "sensor1_index")
df_computer = to_dataframe(data_computer, "computer_index")
df_mistral = to_dataframe(data_mistral, "mistral_index")

# Ανάκτηση δεδομένων πυρκαγιάς με την απαραίτητη επεξεργασία
fire_data = data_computer.get('fire', [])
if fire_data:
    for fire in fire_data:
        fire['BUI'] = fire['BUI'] / 100
        fire['DMC'] = fire['DMC'] / 100
        fire['FFMC'] = fire['FFMC'] / 10000
        fire['FWI'] = fire['FWI'] / 10000
        fire['ISI'] = fire['ISI'] / 10000

# Ανάκτηση περιγραφών εικόνων από το API
photo1_description = None
photo2_description = None
description_text = None

if len(data_mistral) > 0:
    mistral_description = data_mistral[0].get('description', '')
    if 'Δεν μπορώ να σας παράσχω πρόγνωση καιρού με βάση δεδομένα στα οποία δεν έχω δικαίωμα πρόσβασης.' not in mistral_description:
        description_text = mistral_description

    if 'sensor_data' in data_mistral[0] and 'foto1' in data_mistral[0]['sensor_data']:
        photo1_description = data_mistral[0]['sensor_data']['foto1']
    if 'sensor_data' in data_mistral[0] and 'foto2' in data_mistral[0]['sensor_data']:
        photo2_description = data_mistral[0]['sensor_data']['foto2']

# Περιγραφές των δεικτών χωρίς διαίρεση των τιμών
indicator_descriptions = {
    "BUI": "BUI (Build-Up Index): Μια μέτρηση της ικανότητας της οργανικής ύλης να αναφλέγεται και να καίγεται. Μέγιστη τιμή: 200, Ελάχιστη τιμή: 0.",
    "DC": "DC (Drought Code): Ένας δείκτης της μακροχρόνιας ξηρότητας. Μέγιστη τιμή: 1000, Ελάχιστη τιμή: 0.",
    "DMC": "DMC (Duff Moisture Code): Ένας δείκτης της μέσης υγρασίας των καύσιμων υλικών. Μέγιστη τιμή: 150, Ελάχιστη τιμή: 0.",
    "FFMC": "FFMC (Fine Fuel Moisture Code): Ένας δείκτης της υγρασίας των λεπτών καυσίμων υλικών. Μέγιστη τιμή: 101, Ελάχιστη τιμή: 0.",
    "FWI": "FWI (Fire Weather Index): Ένας συνολικός δείκτης της επικινδυνότητας πυρκαγιάς. Μέγιστη τιμή: 150, Ελάχιστη τιμή: 0.",
    "ISI": "ISI (Initial Spread Index): Ένας δείκτης της ταχύτητας εξάπλωσης της πυρκαγιάς. Μέγιστη τιμή: 50, Ελάχιστη τιμή: 0.",
    "PM10": "Αναφέρεται σε αιωρούμενα σωματίδια με διάμετρο μικρότερη ή ίση με 10 μικρόμετρα (μm). Συγκέντρωση: {} μg/m³. Αυτά τα σωματίδια μπορούν να εισχωρήσουν στην αναπνευστική οδό και να προκαλέσουν αναπνευστικά προβλήματα και άλλες υγειονομικές επιπτώσεις.",
    "PM1_0": "Αναφέρεται σε αιωρούμενα σωματίδια με διάμετρο μικρότερη ή ίση με 1 μικρόμετρο (μm). Συγκέντρωση: {} μg/m³. Αυτά τα μικροσκοπικά σωματίδια μπορούν να διεισδύσουν βαθιά στους πνεύμονες και να επηρεάσουν την καρδιαγγειακή υγεία.",
    "PM2_5": "Αναφέρεται σε αιωρούμενα σωματίδια με διάμετρο μικρότερη ή ίση με 2.5 μικρόμετρα (μm). Συγκέντρωση: {} μg/m³. Αυτά τα σωματίδια είναι αρκετά μικρά για να εισχωρήσουν βαθιά στους πνεύμονες και μπορούν να προκαλέσουν σοβαρά αναπνευστικά και καρδιαγγειακά προβλήματα."
}

# Συνάρτηση για τη δημιουργία ρολογιού με Plotly
def create_gauge(value, title, min_value=0, max_value=100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': "lightblue"},
            'steps': [
                {'range': [min_value, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value * 0.75], 'color': "yellow"},
                {'range': [max_value * 0.75, max_value], 'color': "red"}]}))
    return fig

# Εφαρμογή light mode με χρώματα και ωραία γραμματοσειρά
st.markdown(
    """
    <style>
    .main {
        background-color: #f5f5f5;
        color: #333;
        font-family: 'Arial', sans-serif;
        font-size: 18px;
    }
    .header, .subheader {
        color: #0056b3;
        font-family: 'Arial Black', Gadget, sans-serif;
        font-size: 28px;
    }
    .stRadio > div {
        background-color: #e6f7ff;
        border-radius: 5px;
    }
    .stRadio > div label {
        color: #333;
    }
    .css-145kmo2 {
        color: #333;
        font-size: 18px;
    }
    .css-1d391kg h3, .css-1d391kg h4, .css-1d391kg h5, .css-1d391kg h6 {
        color: #333;
    }
    /* Προσαρμογή στυλ για το αριστερό μενού */
    .css-18e3th9 {
        background-color: #0056b3 !important; /* Μπλε χρώμα για το αριστερό μενού */
        color: #ffffff !important; /* Λευκό κείμενο για το αριστερό μενού */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Μετεωρολογικός Σταθμός Μεσολογγίου")
st.write("Παρουσίαση δεδομένων και προβλέψεων με χρήση AI")

# Διάταξη στήλης για μενού πλοήγησης και περιεχόμενο
st.sidebar.header("Μενού")
page = st.sidebar.radio("Επιλέξτε σελίδα:",
                        ["Αρχική Σελίδα", "Αισθητήρας 1", "Αισθητήρας 2", "Εκτίμηση κινδύνου πυρκαγιάς", "Πρόβλεψη θερμοκρασίας", "Μετεωρολογική πρόβλεψη", "Κάμερες", "Ιστορικό"])

if page == "Αρχική Σελίδα":
    st.image("https://www.saekmesol.gr/wp-content/uploads/2024/03/new_site_logo.png", use_column_width=True)
    st.header("Καινοτόμος Μετεωρολογικός Σταθμός: Χρήση Τεχνητής Νοημοσύνης για Εκτίμηση Πρόβλεψης Πυρκαγιών")
    st.write("Γκαναβίας Θεοφάνης, Τσαμαδιάς Σταύρος, Χατζής Ιωάννης, Γκαναβίας Ι. Δημήτριος")
    st.write(
        " Η παρούσα εργασία αναπτυγμένη στο πλαίσιο κατάρτισης της ειδικότητας 'Τεχνικός Λογισμικού ΗΥ' της Σ.Α.Ε.Κ. Μεσολογγίου στοχεύει στην ανάπτυξη ενός καινοτόμου συστήματος πρόβλεψης πυρκαγιών χρησιμοποιώντας μετεωρολογικά δεδομένα και τεχνητή νοημοσύνη. Μέσω αισθητήρων που συλλέγουν κρίσιμα περιβαλλοντικά δεδομένα όπως θερμοκρασία, υγρασία και ταχύτητα ανέμου επιτυγχάνεται η έγκαιρη ανίχνευση και πρόβλεψη των κινδύνων πυρκαγιάς. Η αυτοματοποίηση της διαδικασίας συλλογής και ανάλυσης δεδομένων προσφέρει ακριβείς προβλέψεις οι οποίες είναι δημόσια προσβάσιμες σε πραγματικό χρόνο επιτρέποντας στις Αρχές και στο κοινό να λάβουν άμεσα μέτρα προστασίας. Αυτή η εργασία έχει σημαντικό κοινωνικό και περιβαλλοντικό αντίκτυπο. Η έγκαιρη πρόβλεψη πυρκαγιών προστατεύει ανθρώπινες ζωές και περιουσίες, μειώνει οικονομικές απώλειες και τις εκπομπές αερίων του θερμοκηπίου ενώ διατηρεί τα φυσικά οικοσυστήματα και τη βιοποικιλότητα. Επιπλέον προσέφερε εκπαιδευτικά οφέλη στους καταρτιζόμενους οι οποίοι συμμετείχαν σε όλες τις φάσεις της ανάπτυξης και προωθεί την ενημέρωση σχετικά με τους κινδύνους και τις μεθόδους πρόληψης των φυσικών καταστροφών.")

    # Προσθήκη του χάρτη στο τέλος της περιγραφής
    st.subheader("Τοποθεσία Σταθμού")
    map = folium.Map(location=[38.368059813428324, 21.43681283635912], zoom_start=15)
    folium.Marker([38.368059813428324, 21.43681283635912], tooltip='ΣΑΕΚ Μεσολογγίου').add_to(map)
    folium_static(map)

    st.subheader("Χάρτης Κινδύνου Πυρκαγιάς")
    st.markdown(
        '<iframe src="https://riskmap.beyond-eocenter.eu/mobile_version/index.php" width="100%" height="600px"></iframe>',
        unsafe_allow_html=True
    )

elif page == "Αισθητήρας 1":
    st.header("Δεδομένα από τον Αισθητήρα 1")
    st.dataframe(df_sensor1)

    # Δημιουργία ρολογιών για τους δείκτες
    st.subheader("Ρολόι CO2")
    if 'co2' in df_sensor1.columns:
        fig = create_gauge(df_sensor1['co2'].iloc[0], 'CO2', min_value=0, max_value=5000)
        st.plotly_chart(fig)

    st.subheader("Ρολόι Υγρασίας")
    if 'humidity' in df_sensor1.columns:
        fig = create_gauge(df_sensor1['humidity'].iloc[0], 'Υγρασία', min_value=0, max_value=100)
        st.plotly_chart(fig)

    st.subheader("Ρολόι Θερμοκρασίας")
    if 'temp' in df_sensor1.columns:
        fig = create_gauge(df_sensor1['temp'].iloc[0], 'Θερμοκρασία', min_value=-10, max_value=50)
        st.plotly_chart(fig)

    st.subheader("Ρολόι Ταχύτητας Ανέμου")
    if 'windspeed' in df_sensor1.columns:
        fig = create_gauge(df_sensor1['windspeed'].iloc[0], 'Ταχύτητα Ανέμου', min_value=0, max_value=100)
        st.plotly_chart(fig)

    # Εμφάνιση εικόνας ανάλογα με την κατάσταση βροχής
    st.subheader("Γράφημα Αισθητήρα Βροχής")
    if 'pm2' in df_sensor1.columns:
        rain_status = df_sensor1['pm2'].iloc[0]
        if rain_status == 0:
            st.image(rainy_image_path, caption="Βροχή")
        else:
            st.image(sunny_image_path, caption="Ηλιοφάνεια")

elif page == "Αισθητήρας 2":
    st.header("Δεδομένα από τον Αισθητήρα 2")
    st.dataframe(df_sensor2)

    st.write("""
    Τα αιωρούμενα σωματίδια (PM10, PM2.5, PM1.0) που μετρώνται στον αέρα έχουν διάφορες τιμές ανάλογα με την πηγή και την περιοχή.
    Δεν υπάρχει αυστηρά καθορισμένη μέγιστη και ελάχιστη τιμή, αλλά υπάρχουν ορισμένες κατευθυντήριες γραμμές και πρότυπα που έχουν θεσπιστεί από οργανισμούς όπως ο Παγκόσμιος Οργανισμός Υγείας (ΠΟΥ) και οι εθνικές αρχές για την ποιότητα του αέρα. Ακολουθούν οι κατευθυντήριες γραμμές του ΠΟΥ και γενικές μέγιστες και ελάχιστες τιμές που μπορούν να βρεθούν στην πράξη:

    **PM10**
    - Μέγιστη επιτρεπτή τιμή (κατευθυντήριες γραμμές του ΠΟΥ):
      - 24ωρη μέση τιμή: 50 μg/m³
      - Ετήσια μέση τιμή: 20 μg/m³
    - Πρακτικά παρατηρούμενες τιμές:
      - Μέγιστη τιμή: Μπορεί να υπερβεί τα 500 μg/m³ σε εξαιρετικά μολυσμένες περιοχές ή σε περιόδους έντονης ατμοσφαιρικής ρύπανσης (π.χ. από πυρκαγιές, σκόνη).
      - Ελάχιστη τιμή: 0 μg/m³ (σε πολύ καθαρές περιοχές ή κατά τη διάρκεια μηδενικής ρύπανσης).

    **PM2.5**
    - Μέγιστη επιτρεπτή τιμή (κατευθυντήριες γραμμές του ΠΟΥ):
      - 24ωρη μέση τιμή: 25 μg/m³
      - Ετήσια μέση τιμή: 10 μg/m³
    - Πρακτικά παρατηρούμενες τιμές:
      - Μέγιστη τιμή: Μπορεί να υπερβεί τα 300 μg/m³ σε εξαιρετικά μολυσμένες περιοχές ή σε περιόδους έντονης ατμοσφαιρικής ρύπανσης.
      - Ελάχιστη τιμή: 0 μg/m³ (σε πολύ καθαρές περιοχές ή κατά τη διάρκεια μηδενικής ρύπανσης).

    **PM1.0**
    - Μέγιστες και ελάχιστες τιμές:
      - Δεν υπάρχουν συγκεκριμένες κατευθυντήριες γραμμές από τον ΠΟΥ για τα PM1.0, αλλά γενικά οι τιμές τους είναι χαμηλότερες από τις τιμές των PM2.5 και PM10.
      - Μέγιστη τιμή: Μπορεί να φτάσει υψηλές τιμές σε περιόδους έντονης ατμοσφαιρικής ρύπανσης, συνήθως έως 100-150 μg/m³.
      - Ελάχιστη τιμή: 0 μg/m³ (σε πολύ καθαρές περιοχές ή κατά τη διάρκεια μηδενικής ρύπανσης).

    Αυτές οι τιμές είναι ενδεικτικές και μπορούν να ποικίλουν
    ανάλογα με την τοποθεσία, την εποχή και τις πηγές ρύπανσης. Οι τιμές πάνω από τα όρια που καθορίζονται από τον ΠΟΥ θεωρούνται ανθυγιεινές και μπορούν να έχουν αρνητικές επιπτώσεις στην ανθρώπινη υγεία.
    """)

    # Δημιουργία ραβδογραφημάτων για τους δείκτες ατμοσφαιρικών σωματιδίων
    st.subheader("Ραβδογράφημα PM10")
    if 'PM10' in df_sensor2.columns:
        fig = go.Figure(data=[go.Bar(x=['PM10'], y=[df_sensor2['PM10'].iloc[0]], marker_color='red')])
        fig.update_layout(title='Συγκέντρωση PM10 (μg/m³)', yaxis=dict(range=[0, 500]))
        st.plotly_chart(fig)
        st.write(indicator_descriptions['PM10'].format(df_sensor2['PM10'].iloc[0]))

    st.subheader("Ραβδογράφημα PM1.0")
    if 'PM1_0' in df_sensor2.columns:
        fig = go.Figure(data=[go.Bar(x=['PM1.0'], y=[df_sensor2['PM1_0'].iloc[0]], marker_color='blue')])
        fig.update_layout(title='Συγκέντρωση PM1.0 (μg/m³)', yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig)
        st.write(indicator_descriptions['PM1_0'].format(df_sensor2['PM1_0'].iloc[0]))

    st.subheader("Ραβδογράφημα PM2.5")
    if 'PM2_5' in df_sensor2.columns:
        fig = go.Figure(data=[go.Bar(x=['PM2.5'], y=[df_sensor2['PM2_5'].iloc[0]], marker_color='green')])
        fig.update_layout(title='Συγκέντρωση PM2.5 (μg/m³)', yaxis=dict(range=[0, 300]))
        st.plotly_chart(fig)
        st.write(indicator_descriptions['PM2_5'].format(df_sensor2['PM2_5'].iloc[0]))

elif page == "Εκτίμηση κινδύνου πυρκαγιάς":
    st.header("Δεδομένα από το FWI (Fire Weather Index)")
    st.write(
        "Ο δείκτης καιρικών συνθηκών πυρκαγιάς (Fire Weather Index - FWI) είναι ένα μετρικό σύστημα που χρησιμοποιείται για την πρόβλεψη των κινδύνων πυρκαγιάς. Περιλαμβάνει διάφορους δείκτες που λαμβάνουν υπόψη τη θερμοκρασία, την υγρασία, την ταχύτητα του ανέμου και άλλους παράγοντες.")

    # Εμφάνιση των δεδομένων πυρκαγιάς
    st.subheader("Δεδομένα Πυρκαγιάς")
    if fire_data:
        fire_df = pd.DataFrame(fire_data)
        st.dataframe(fire_df)
        for fire in fire_data:
            st.write(f"**Ημερομηνία και Ώρα:** {fire['datetime']}")
            st.write(f"**BUI (Building Ignition Sub-layer):** {fire['BUI']}")
            st.write(f"**DC (Drought Code):** {fire['DC']}")
            st.write(f"**DMC (Duff Moisture Code):** {fire['DMC']}")
            st.write(f"**FFMC (Fine Fuel Moisture Code):** {fire['FFMC']}")
            st.write(f"**FWI (Fire Weather Index):** {fire['FWI']}")
            st.write(f"**ISI (Initial Spread Index):** {fire['ISI']}")
            st.write("---")

        # Δημιουργία ιστόγραμματος για τους δείκτες
        st.subheader("Ιστόγραμμα Δεικτών Πυρκαγιάς")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=['BUI', 'DC', 'DMC', 'FFMC', 'FWI', 'ISI'],
            y=[fire_df['BUI'].iloc[0], fire_df['DC'].iloc[0], fire_df['DMC'].iloc[0], fire_df['FFMC'].iloc[0],
               fire_df['FWI'].iloc[0], fire_df['ISI'].iloc[0]],
            marker_color='indianred'
        ))

        fig.update_layout(
            title='Ιστόγραμμα Δεικτών Πυρκαγιάς',
            xaxis_title='Δείκτες',
            yaxis_title='Τιμή'
        )

        st.plotly_chart(fig)

        # Προσθήκη περιγραφών των δεικτών κάτω από το ιστόγραμμα
        for indicator in ['BUI', 'DC', 'DMC', 'FFMC', 'FWI', 'ISI']:
            st.markdown(f"**{indicator}:** {indicator_descriptions[indicator]}")

    else:
        st.write("Δεν υπάρχουν διαθέσιμα δεδομένα πυρκαγιάς.")

elif page == "Πρόβλεψη θερμοκρασίας":
    st.header("Προβλέψεις Θερμοκρασίας με Χρήση Neural Networks με τα μοντέλα Holt-Winter & Prophet της Facebook")

    # Περιγραφή των μοντέλων
    st.write("""
    **Holt-Winter Μοντέλο:**
    Το μοντέλο Holt-Winter χρησιμοποιείται για την πρόβλεψη των μέγιστων θερμοκρασιών. Το μοντέλο αυτό είναι γνωστό για την ικανότητά του να προβλέπει εποχιακά δεδομένα, λαμβάνοντας υπόψη τάσεις και εποχικότητες.

    **Prophet Μοντέλο από το Facebook:**
    Το Prophet είναι ένα μοντέλο προβλέψεων που αναπτύχθηκε από το Facebook, και χρησιμοποιείται για την πρόβλεψη των ελάχιστων θερμοκρασιών. Το μοντέλο αυτό είναι ιδιαίτερα αποτελεσματικό στην αντιμετώπιση δεδομένων με έντονη εποχικότητα και ανωμαλίες.
    """)

    # URL JSON data
    url = "https://stayrostsamadias.pythonanywhere.com/data"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    else:
        st.error(f"Error fetching data from {url}. Status code: {response.status_code}")

    # Extracting data
    forecast_data = data['forecast']
    holt_winder_data = data['holt_winder']

    # Convert forecast data to DataFrame
    forecast_df = pd.DataFrame(forecast_data)
    forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])

    # Convert holt_winder data to DataFrame
    holt_winder_df = pd.DataFrame(holt_winder_data)
    holt_winder_df['Unnamed: 0'] = pd.to_datetime(holt_winder_df['Unnamed: 0'])

    # Plotting the data
    plt.figure(figsize=(12, 6))

    # Plotting forecast data
    plt.plot(forecast_df['ds'], forecast_df['Forecast'], label='Neural Networks Forecast (Min Temperature)', marker='o')

    # Plotting holt_winder data
    plt.plot(holt_winder_df['Unnamed: 0'], holt_winder_df['Forecast'], label='Holt-Winter Forecast (Max Temperature)',
             marker='o')

    # Adding labels and title
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.title('Σύγκριση Προβλέψεων Θερμοκρασίας')
    plt.legend()
    plt.grid(True)

    # Display the plot
    st.pyplot(plt)

elif page == "Μετεωρολογική πρόβλεψη":
    st.header("Δεδομένα από το Μοντέλο Mistral")
    st.image("meteorologos.webp", caption="Μετεωρολόγος")
    st.write(description_text or "Περιγραφή δεν είναι διαθέσιμη")

elif page == "Κάμερες":
    st.header("Εικόνες από τις Κάμερες")

    st.markdown('<div class="image-container">', unsafe_allow_html=True)
    st.image("https://tsamadias1982.pythonanywhere.com/live_video_camera1", caption="Κάμερα 1")
    st.markdown(f"""<div class="image-text">{photo1_description or "Περιγραφή δεν είναι διαθέσιμη"}</div>""",
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="image-container">', unsafe_allow_html=True)
    st.image("https://tsamadias1982.pythonanywhere.com/live_video_camera2", caption="Κάμερα 2")
    st.markdown(f"""<div class="image-text">{photo2_description or "Περιγραφή δεν είναι διαθέσιμη"}</div>""",
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Ιστορικό":
    st.header("Ιστορικό Θερμοκρασιών")

    # Διαβάστε το αρχείο Excel
    excel_file_path = "updated_histori.xlsx"
    df_excel = pd.read_excel(excel_file_path)

    # Έλεγχος αν η στήλη 'datetime' υπάρχει στο αρχείο Excel
    if 'datetime' not in df_excel.columns:
        st.error("Η στήλη 'datetime' δεν βρέθηκε στο αρχείο Excel.")
    else:
        # Μετατροπή της στήλης 'datetime' σε τύπο datetime
        df_excel['datetime'] = pd.to_datetime(df_excel['datetime'], errors='coerce')

        # Ανάκτηση νέων δεδομένων από το API
        fire_df = pd.DataFrame(fire_data)
        fire_df['datetime'] = pd.to_datetime(fire_df['datetime'], errors='coerce')

        # Βεβαιωθείτε ότι οι στήλες 'datetime' και 'temperature_2m (°C)' υπάρχουν στα δεδομένα
        if 'temperature_2m' in fire_df.columns:
            new_data = fire_df[['datetime', 'temperature_2m']]

            # Συνδυασμός των δεδομένων χωρίς διπλότυπα
            combined_df = pd.concat(
                [df_excel[['datetime', 'temperature_2m']], new_data]).drop_duplicates().reset_index(drop=True)

            # Αποθηκεύστε τα ενημερωμένα δεδομένα πίσω στο Excel
            combined_df.to_excel(excel_file_path, index=False)

            # Δημιουργία γραφημάτων για περσινές και φετινές θερμοκρασίες
            st.subheader("Περσινές Θερμοκρασίες")
            last_year = (pd.to_datetime("today") - pd.DateOffset(years=1)).year
            last_year_data = combined_df[combined_df['datetime'].dt.year == last_year]
            fig_last_year = px.line(last_year_data, x='datetime', y='temperature_2m',
                                    title="Περσινές Θερμοκρασίες")
            st.plotly_chart(fig_last_year)

            st.subheader("Φετινές Θερμοκρασίες")
            current_year = pd.to_datetime("today").year
            this_year_data = combined_df[combined_df['datetime'].dt.year == current_year]
            fig_this_year = px.line(this_year_data, x='datetime', y='temperature_2m', title="Φετινές Θερμοκρασίες")
            st.plotly_chart(fig_this_year)
        else:
            st.error("Η στήλη 'temperature_2m (°C)' δεν βρέθηκε στα δεδομένα API.")
