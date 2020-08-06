FROM python:3.8

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir /code
WORKDIR /code

# Install dependencies:
COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY example/* ./

RUN mkdir xml

# Run the application:
CMD ["python", "vl-to-ojs-xml-exporter.py"]
