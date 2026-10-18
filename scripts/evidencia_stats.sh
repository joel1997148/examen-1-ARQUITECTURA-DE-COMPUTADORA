#!/usr/bin/env bash
# Levanta el contenedor con los límites de compose.yaml, genera algo de carga
# y guarda la evidencia de `docker stats` e `docker inspect` en evidencias/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidencias

docker compose up -d --build
echo "Esperando a que el contenedor esté saludable..."
for _ in $(seq 1 30); do
  estado=$(docker inspect -f '{{.State.Health.Status}}' analizador-datos 2>/dev/null || echo starting)
  [ "$estado" = "healthy" ] && break
  sleep 2
done

# Carga ligera: 200 peticiones a la página principal
for _ in $(seq 1 200); do curl -s -o /dev/null http://localhost:8000/; done

{
  echo "# Evidencia generada el $(date -Iseconds)"
  echo
  echo "## docker stats --no-stream"
  docker stats --no-stream --format \
    "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.PIDs}}" analizador-datos
  echo
  echo "## Límites aplicados (docker inspect)"
  docker inspect -f 'Memoria={{.HostConfig.Memory}} bytes  NanoCPUs={{.HostConfig.NanoCpus}}  SoloLectura={{.HostConfig.ReadonlyRootfs}}  Usuario={{.Config.User}}' analizador-datos
} | tee evidencias/docker_stats.txt

echo "Evidencia guardada en evidencias/docker_stats.txt (tome también una captura de pantalla)."
