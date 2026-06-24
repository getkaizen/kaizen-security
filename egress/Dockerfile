FROM python:3.12-slim
WORKDIR /app
COPY proxy.py .
ENV PORT=8080
EXPOSE 8080
CMD ["python", "proxy.py"]
