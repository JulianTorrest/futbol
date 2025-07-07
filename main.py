import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- Configuración de la API ---
API_KEY = "dc98474508c65500e4a8776d96a76a5e"
BASE_URL = "https://v3.football.api-sports.io/"

# Puedes ajustar los headers según lo que te haya funcionado (x-apisports-key o x-rapidapi-key)
# Prefiero 'x-apisports-key' para acceso directo, pero si usaste RapidAPI, 'x-rapidapi-key' es el indicado.
# Si el código anterior con x-rapidapi-key te funcionó, usa esos headers.
HEADERS = {
    'x-apisports-key': API_KEY,
    # Si 'x-rapidapi-key' y 'x-rapidapi-host' te funcionaron, usa estos en su lugar:
    # 'x-rapidapi-key': API_KEY,
    # 'x-rapidapi-host': "v3.football.api-sports.io"
}

# --- Funciones para la interacción con la API ---

@st.cache_data(ttl=3600) # Almacena en caché los resultados por 1 hora para evitar llamadas repetidas
def fetch_data(endpoint, params=None):
    """
    Función genérica para hacer llamadas a la API de Football.
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()  # Lanza una excepción para errores HTTP (4xx o 5xx)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al consultar {endpoint}: {http_err}")
        st.error(f"Contenido de la respuesta: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        st.error(f"Error de conexión/petición al consultar {endpoint}: {req_err}")
        return None
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al consultar {endpoint}: {e}")
        return None

def get_leagues():
    """
    Obtiene la lista de ligas disponibles.
    """
    data = fetch_data("leagues")
    if data and data['response']:
        return data['response']
    return []

def get_fixtures(league_id, season, status="FT", date_from=None, date_to=None):
    """
    Obtiene los partidos (fixtures) para una liga y temporada específicas.
    Permite filtrar por estado (ej. 'FT' para Finalizado) y rango de fechas.
    """
    params = {
        "league": league_id,
        "season": season,
        "status": status # Por defecto, buscamos partidos terminados
    }
    if date_from:
        params["from"] = date_from.strftime("%Y-%m-%d")
    if date_to:
        params["to"] = date_to.strftime("%Y-%m-%d")

    data = fetch_data("fixtures", params)
    if data and data['response']:
        return data['response']
    return []

# --- Configuración de la interfaz de Streamlit ---

st.set_page_config(
    page_title="Historial de Eventos de Fútbol",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Historial de Eventos de Fútbol (API-Sports)")

st.write("""
Esta aplicación te permite explorar datos de ligas y partidos de fútbol
utilizando la API de API-Sports.
""")

# --- Sección: Listado de Ligas ---
st.header("🔍 Ligas Disponibles")
st.write("Aquí puedes ver una lista de las ligas a las que puedes acceder.")

if st.button("Cargar Ligas"):
    with st.spinner("Cargando ligas..."):
        leagues = get_leagues()
        if leagues:
            # Crear un DataFrame para una mejor visualización
            leagues_df = pd.DataFrame([
                {
                    "ID": l['league']['id'],
                    "Nombre": l['league']['name'],
                    "Tipo": l['league']['type'],
                    "País": l['country']['name'],
                    "Logo": l['league']['logo'] # Incluir el logo para posible visualización
                }
                for l in leagues
            ])
            st.dataframe(leagues_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No se pudo obtener la información de las ligas. Por favor, revisa tu API Key y la conexión.")

st.markdown("---")

# --- Sección: Búsqueda de Partidos Históricos ---
st.header("🗓️ Buscar Partidos Históricos")
st.write("Selecciona una liga y una temporada para obtener los partidos finalizados.")

# 1. Selector de Liga
leagues = get_leagues() # Obtener las ligas una vez para el selector
league_options = {l['league']['name']: l['league']['id'] for l in leagues}

selected_league_name = st.selectbox(
    "Selecciona una Liga:",
    options=list(league_options.keys())
)
selected_league_id = league_options.get(selected_league_name)

# 2. Selector de Temporada
# La API suele usar el año de inicio de la temporada (ej. 2023 para 2023/2024)
current_year = datetime.now().year
years = list(range(current_year, 2009, -1)) # Desde el año actual hasta 2009, o el que la API soporte
selected_season = st.selectbox(
    "Selecciona una Temporada:",
    options=years
)

# 3. Rango de Fechas (Opcional, para refinar la búsqueda si la temporada es muy grande)
st.subheader("Filtrar por Rango de Fechas (Opcional)")
col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("Fecha de Inicio:", value=None, min_value=datetime(1990, 1, 1), max_value=datetime.now() + timedelta(days=365))
with col2:
    date_to = st.date_input("Fecha Fin:", value=None, min_value=datetime(1990, 1, 1), max_value=datetime.now() + timedelta(days=365))


if st.button("Buscar Partidos"):
    if selected_league_id and selected_season:
        with st.spinner(f"Buscando partidos para {selected_league_name} ({selected_season})..."):
            fixtures = get_fixtures(selected_league_id, selected_season, "FT", date_from, date_to) # Solo partidos Finalizados (FT)

            if fixtures:
                st.subheader(f"Partidos Finalizados de {selected_league_name} - Temporada {selected_season}")

                # Preparar datos para DataFrame
                fixture_data = []
                for f in fixtures:
                    fixture_data.append({
                        "ID Partido": f['fixture']['id'],
                        "Fecha": pd.to_datetime(f['fixture']['date']).strftime("%Y-%m-%d %H:%M"),
                        "Estadio": f['fixture']['venue']['name'],
                        "Equipo Local": f['teams']['home']['name'],
                        "Goles Local": f['goals']['home'],
                        "Goles Visitante": f['goals']['away'],
                        "Equipo Visitante": f['teams']['away']['name'],
                        "Estado": f['fixture']['status']['short'],
                        "Temporada": f['league']['season'],
                        "Ronda": f['league']['round']
                    })
                fixtures_df = pd.DataFrame(fixture_data)
                st.dataframe(fixtures_df, use_container_width=True, hide_index=True)

                st.success(f"Se encontraron {len(fixtures)} partidos.")
            else:
                st.warning(f"No se encontraron partidos finalizados para {selected_league_name} en la temporada {selected_season} con los filtros seleccionados.")
    else:
        st.error("Por favor, selecciona una liga y una temporada.")

st.markdown("---")
st.info("💡 **Consejo:** Los datos de la API pueden tener límites de tasa. El caché ayuda a reducir las llamadas repetidas.")
st.caption("Desarrollado para almacenamiento de información histórica de eventos deportivos.")
