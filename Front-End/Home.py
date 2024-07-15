import streamlit as st
import pandas as pd

# Título de la página
st.title("Página de Inicio - Tecnologías Utilizadas")

st.write("""
Bienvenidos a nuestra página de inicio. Aquí hacemos referencia a varias tecnologías que utilizamos en nuestros proyectos.
""")

data = {
    "Tecnología": ["Python", "Streamlit", "Pandas", "Plotly", "Docker", "Redis", "Flask", "Pickle"],
    "Descripción": [
        "Python es un lenguaje de programación de alto nivel, interpretado y de propósito general.",
        "Streamlit es una biblioteca de Python que permite crear aplicaciones web interactivas de manera fácil y rápida.",
        "Pandas es una biblioteca de Python para la manipulación y análisis de datos.",
        "Plotly es una biblioteca de visualización que permite crear gráficos interactivos y bonitos.",
        "Docker es una plataforma para desarrollar, enviar y ejecutar aplicaciones dentro de contenedores.",
        "Redis es una base de datos en memoria que se usa como almacenamiento de estructura de datos, caché y agente de mensajes.",
        "Flask es un micro framework de desarrollo web para Python que permite crear aplicaciones web rápidamente.",
        "Pickle es un módulo de Python que se utiliza para serializar y deserializar estructuras de objetos de Python."
    ],
    "Imagen": [
        "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png",
        "https://streamlit.io/images/brand/streamlit-mark-color.png",
        "https://pandas.pydata.org/static/img/pandas_mark.svg",
        "https://images.plot.ly/logo/new-branding/plotly-logomark.png",
        "https://bunnyacademy.b-cdn.net/what-is-docker.png",
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRB1eNr3uquRKdHqS-4s57YQm3q7egkSbzqrrL8glA0pGvB_I5u3h91Eg1GtaRd9BezJ2w&usqp=CAU",
        "https://flask.palletsprojects.com/en/2.0.x/_images/flask-logo.png",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjP7ad9RpHCWpERjIaL8Cshu0uKGpxdIoHAdZA_mG_j_56aEbHeRvMuZFiZZPqe-8owHvMpXiqgvwRsGW9X7f62VgynIBMyBgY1qrca-_SCoeWNiStvgbwziAhaqBF7EqQBFJP89E-OuHk/s1600/python-pickle-800x2001.png"
    ]
}

df = pd.DataFrame(data)

# Mostrar tarjetas
st.write("## Más Información sobre las Tecnologías")

for i in range(0, len(df), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(df):
            with cols[j]:
                st.markdown(f"""
                <div class="card">
                    <img src="{df['Imagen'][i + j]}" alt="{df['Tecnología'][i + j]}" style="width:100%; height:150px; object-fit:contain;">
                    <div class="container">
                        <h4><b>{df['Tecnología'][i + j]}</b></h4> 
                        <p>{df['Descripción'][i + j]}</p> 
                        <a href="https://www.google.com/search?q={df['Tecnología'][i + j]}" class="btn" target="_blank">Más Información</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Información del equipo
st.title('Equipo: ')
st.subheader("Bryan Resendiz Rodriguez")
st.subheader("José Ángel Martínez Figueroa")
st.subheader("Cristopher Fernando Santiago Cruz")
st.subheader("Jorge Alberto Mendoza Ramírez")
st.subheader("Ernesto Rodríguez Rocha")

# Mensaje de agradecimiento
st.write("""
Gracias por visitar nuestra página. Si tienes alguna pregunta o comentario, no dudes en ponerte en contacto con nosotros.
""")
