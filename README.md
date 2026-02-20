# Crypto Tracker

Aplicação demo que monitora o preço do Bitcoin e grava o histórico em PostgreSQL. O projeto é dividido em três camadas principais:

- **API Flask** (`app/api`): expõe a rota `/history` para consultar os registros salvos e realiza o bootstrap do schema (cria a tabela `registro_valores` se não existir).
- **Worker** (`app/worker`): busca o preço atual via CoinGecko a cada 30 segundos e insere no banco na mesma tabela `registro_valores`.
- **Infraestrutura** (`infra` e `k8s`): provisiona um cluster Kind gerenciado por Terraform, instala Argo CD + stack Prometheus/Grafana via Helm e aplica os manifestos Kubernetes dos serviços.

## Tech Stack

- Python 3.11, Flask, psycopg2, Requests
- PostgreSQL 16
- Docker + Docker Compose (imagens customizadas para API e worker)
- Kind + Terraform + Helm
- Kubernetes (Deployments, Services, Secrets)
- Argo CD e kube-prometheus-stack para observabilidade

## Estrutura do Repositório

```
app/
  api/
    Dockerfile
    main.py
    requirements.txt
  worker/
    Dockerfile
    main.py
    requirements.txt
infra/
  main.tf           # Provisiona cluster Kind e instala ArgoCD + monitoring via Helm
k8s/
  api.yaml          # Deployment + Service da API
  worker.yaml       # Deployment do worker
  secrets.yaml      # DATABASE_URL usado pelos pods
docker-compose.yml  # Placeholder para futuros usos locais
```

## Como o sistema funciona (visão simples)

Fluxo geral:

1. O **worker** chama periodicamente a API pública da CoinGecko e pega o preço atual do Bitcoin em dólar.
2. O worker grava cada preço na tabela `registro_valores` do PostgreSQL (colunas: `id`, `symbol`, `valor`, `created_at`).
3. A **API Flask** lê esses registros do banco e expõe tudo na rota `/history` em formato JSON.
4. O **Grafana** se conecta ao PostgreSQL e exibe gráficos com a evolução do preço ao longo do tempo.

Principais arquivos de código:

- `app/api/main.py`
  - Cria a tabela `registro_valores` se ela ainda não existir (`ensure_schema`).
  - Rota `/` (health check): responde se a API está viva.
  - Rota `/history`: faz `SELECT symbol, valor, created_at FROM registro_valores ...` e devolve uma lista JSON.
- `app/worker/main.py`
  - Busca `bitcoin.usd` na CoinGecko a cada 30s.
  - Insere em `registro_valores (symbol, valor)` usando a mesma variável de ambiente `DATABASE_URL` da API.

## Pré-requisitos

1. Docker & Docker Compose
2. Terraform >= 1.6
3. kubectl
4. Kind
5. Conta no Docker Hub (ou registry compatível) caso deseje publicar as imagens `augusto-idalgo/crypto-api` e `augusto-idalgo/crypto-worker`.

## Build das Imagens

Dentro de cada pasta de serviço:

```bash
# API
cd app/api
python -m pip install -r requirements.txt  # opcional para uso local
docker build -t augusto-idalgo/crypto-api:v1 .

# Worker
cd ../worker
docker build -t augusto-idalgo/crypto-worker:v1 .
```

Publique em um registry acessível ao cluster, se necessário:

```bash
docker push augusto-idalgo/crypto-api:v1
docker push augusto-idalgo/crypto-worker:v1
```

## Subindo tudo localmente com Docker Compose (modo simples)

Se você quiser apenas testar localmente, sem Kind/Kubernetes, pode usar o `docker-compose.yml`:

```bash
cd /home/augusto-idalgo/Documentos/projetoBit
docker compose up --build
```

Isso sobe:

- `postgres`: banco PostgreSQL com volume persistente.
- `api`: Flask rodando em `http://localhost:5000`.
- `worker`: processo em background gravando preços no banco.

Testes rápidos:

- Health check da API:

  ```bash
  curl http://localhost:5000/
  ```

- Histórico de preços (JSON):

  ```bash
  curl http://localhost:5000/history
  ```

## Provisionando o Cluster (Terraform + Kind)

```bash
cd infra
terraform init
terraform apply
```

O `main.tf` atual:

1. Baixa os providers `kind` e `helm`.
2. Cria um cluster Kind chamado `crypto-tracker-cluster`.
3. Configura o provider Helm para falar com o novo cluster.
4. Instala Argo CD (`argocd` namespace) com `server.extraArgs = --insecure` para facilitar o acesso local.
5. Instala `kube-prometheus-stack` no namespace `monitoring`.

Após o `apply`, valide o acesso:

```bash
kubectl get nodes
kubectl get pods -A
```

## Aplicando os manifestos da aplicação

```bash
# Certifique-se de estar no contexto kubeconfig criado pelo Kind
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/worker.yaml
```

> Dica: ajuste os nomes das imagens nos YAMLs caso versione novas tags.

## Configurações Importantes

- `DATABASE_URL`: string no formato `postgresql://USER:PASS@HOST:PORT/DB` consumida tanto pela API quanto pelo worker.
- A API garante que a tabela `registro_valores` exista ao subir (via `ensure_schema`).
- O worker também escreve na tabela `registro_valores` (colunas `symbol` e `valor`), mantendo o schema consistente com a API.

## Próximos Passos

- Popular `docker-compose.yml` para um ambiente local completo.
- Adicionar pipelines de CI/CD usando Argo CD ou GitHub Actions.
- Expandir dashboards do Grafana e alertas do Prometheus conforme as métricas disponibilizadas.

Ficou com dúvidas ou quer contribuir? Abra uma issue ou envie um PR! 🚀
