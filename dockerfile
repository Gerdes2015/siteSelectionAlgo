# Use a Python base image with Bookworm
FROM python:3.11-bookworm

# Set working directory inside the container
WORKDIR /app

# Install GLPK and build tools
RUN apt-get update && apt-get install -y \
    wget build-essential libgmp-dev libmpfr-dev libmpc-dev \
    && wget http://ftp.gnu.org/gnu/glpk/glpk-5.0.tar.gz \
    && tar -xvzf glpk-5.0.tar.gz \
    && cd glpk-5.0 \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /var/lib/apt/lists/* glpk-5.0 glpk-5.0.tar.gz

# Ensure the GLPK library path is available for dynamic linking
ENV LD_LIBRARY_PATH="/usr/local/lib"

# Set GLPK binary in the PATH for use in Pyomo
ENV PATH="/usr/local/bin:${PATH}"

# Copy the entire project after setting up the environment
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit UI with proper server binding
CMD ["streamlit", "run", "frontend/streamlit_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
