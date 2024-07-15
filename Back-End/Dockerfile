# Usa una imagen base de Python
FROM python:3.12

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos
COPY requirements.txt ./

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el contenido del Back-End
COPY . .

# Expone el puerto necesario (ajusta según el puerto que usa tu back-end)
EXPOSE 5000

# Comando para ejecutar la aplicación Back-End
CMD ["python", "Main.py"]
