# Low-Latency Exchange Engine

Deployment Link: https://low-latency-trading-platform.vercel.app/

## Table of Contents

- [Project Description](#project-description)
- [Objectives](#objectives)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Environment Variables](#environment-variables)
- [Run Locally](#run-locally)
- [Tech Stack](#tech-stack)
- [Performance & Benchmarks](#performance--benchmarks)
- [Monitoring & Observability](#monitoring--observability)
- [Screenshots](#screenshots)

## Project Description

> Low-Latency Trading Platform is a high-performance exchange system designed to simulate the core functionality of a real-world electronic trading exchange. The platform implements an in-memory order book with price-time priority, FIFO matching, order execution, risk management, settlement, persistence, and real-time market data.

The project also provides a web-based trading portal for interacting with the exchange and an observability layer using Prometheus and Grafana for monitoring exchange performance, order activity, trade execution, and latency.

## Objectives

> - Build a low-latency exchange engine capable of processing high volumes of orders efficiently.
> - Implement a realistic price-time priority matching engine with FIFO order execution.
> - Provide a web-based trading portal for submitting and managing orders.
> - Implement risk checks, balance/position reservations, and trade settlement.
> - Provide persistence and recovery mechanisms using WAL and event replay.
> - Monitor exchange performance and operational metrics using Prometheus and Grafana.

## Features

> ### Trading Engine
> - In-memory order book with **price-time priority** and FIFO matching.
> - Support for **limit and market orders**.
> - Full and partial order execution.
> - Order cancellation and complete order lifecycle management.
>
> ### Account & Risk Management
> - Account creation and balance management.
> - Cash and position tracking.
> - Pre-trade risk checks.
> - Cash and asset reservation for open orders.
> - Trade settlement with updated balances and positions.
>
> ### Persistence & Recovery
> - Write-Ahead Logging (WAL) for exchange events.
> - Event recording and replay.
> - Exchange state recovery after restart.
> - Persistent account, position, and authentication data using SQLite.
>
> ### Real-Time Trading Portal
> - Web-based trading interface built with **Next.js** and **TypeScript**.
> - Live order book and trade information.
> - Order submission and cancellation.
> - Account balance and portfolio information.
> - Real-time market updates using **WebSockets**.
> - Live price chart for executed trades.
>
> ### Monitoring & Observability
> - Prometheus metrics for exchange activity.
> - Grafana dashboards for monitoring system performance.
> - Order throughput and trade volume monitoring.
> - Order processing latency metrics.
> - Active orders, rejected orders, and cancelled orders tracking.
>
> ### Testing & Performance
> - Comprehensive automated test suite.
> - Unit and integration testing of exchange components.
> - Benchmarking for matching-engine and end-to-end performance.
> - Performance analysis of WAL persistence overhead.

## Technologies Used

> ### Backend & Trading Engine
> - **Python 3.13** — Core exchange engine and backend development.
> - **FastAPI** — REST API and WebSocket services.
> - **Uvicorn** — ASGI server for running the backend.
>
> ### Trading & Data Management
> - **SQLite** — Persistent storage for accounts, positions, and authentication data.
> - **Write-Ahead Logging (WAL)** — Durable event logging and exchange recovery.
> - **WebSockets** — Real-time market data and trading updates.
>
> ### Frontend
> - **Next.js** — Web-based trading portal.
> - **TypeScript** — Type-safe frontend development.
> - **Tailwind CSS** — Frontend styling and responsive UI.
> - **Recharts** — Real-time price chart visualization.
>
> ### Monitoring & Infrastructure
> - **Prometheus** — Exchange metrics collection and monitoring.
> - **Grafana** — Performance and operational dashboards.
> - **Docker** — Containerization of the exchange backend.
> - **Docker Compose** — Local infrastructure and service orchestration.
>
> ### Testing & Development
> - **Pytest** — Automated testing.
> - **Git & GitHub** — Version control and source-code management.
> - **Vercel** — Frontend deployment.
> - **Render** — Backend deployment.

## Environment Variables

> To run this project, create a `.env` file in the project root and add the required environment variables.

### Backend Environment Variables

- `JWT_SECRET` : Secret key used for signing and validating authentication tokens.

> **Note:** The application automatically generates and persists the JWT secret in the `data/` directory when running locally if one is not already configured.

### Frontend Environment Variables

- `NEXT_PUBLIC_API_URL` : Base URL of the exchange backend API.
- `NEXT_PUBLIC_WS_URL` : WebSocket URL used for real-time exchange updates.

### Example

```env
JWT_SECRET=your-secret-key

NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8001/ws

## Run Locally

### Clone the project

```bash
git clone https://github.com/badal-coder/Low-Latency-Trading-Platform.git
cd Low-Latency-Trading-Platform
```

### Create and activate a virtual environment

```bash
python -m venv .venv
```

For Windows:

```powershell
.venv\Scripts\activate
```

### Install backend dependencies

```powershell
pip install -r requirements.txt
```

### Start the backend server

```powershell
python -m uvicorn engine.api:app --port 8001
```

The backend API will run at:

`http://127.0.0.1:8001`

Swagger API documentation:

`http://127.0.0.1:8001/docs`

### Start the trading portal

Open a new terminal:

```powershell
cd Low-Latency-Trading-Platform\portal
npm install
npm run dev -- -p 3001
```

The trading portal will run at:

`http://localhost:3001`

### Run with Docker Compose

```powershell
docker compose up --build
```

To stop the services:

```powershell
docker compose down
```

## Tech Stack

| Category | Technologies |
|---|---|
| **Programming Language** | Python 3.13 |
| **Backend Framework** | FastAPI, Uvicorn |
| **Trading Engine** | Custom In-Memory Order Book, FIFO, Price-Time Priority |
| **Database** | SQLite |
| **Persistence** | Write-Ahead Log (WAL), Event Recording & Replay |
| **Authentication** | JWT, PBKDF2 Password Hashing |
| **Real-Time Communication** | WebSockets |
| **Frontend** | Next.js, TypeScript |
| **Styling** | Tailwind CSS |
| **Charts** | Recharts |
| **Monitoring** | Prometheus, Grafana |
| **Containerization** | Docker, Docker Compose |
| **Testing** | Pytest |
| **Version Control** | Git, GitHub |
| **Frontend Deployment** | Vercel |
| **Backend Deployment** | Render |

## Screenshots

### Trading Portal

### Registration Page

- **Registration**

  The registration page allows users to securely register them into trading platform
<img width="1896" height="905" alt="Screenshot 2026-09-06 114907" src="https://github.com/user-attachments/assets/475be309-82df-4086-9c47-5683bc33aaf3" />


 
### Login Page

- **User Login**

  The login page allows users to securely access the trading platform using their registered credentials.

 <img width="1919" height="893" alt="Screenshot 2026-09-06 114840" src="https://github.com/user-attachments/assets/3b0744a2-bd65-4ad0-8046-79cc5bcc67e9" />

### Trading Dashboard

The main trading dashboard provides an overview of the BTC/USD market, live market statistics, price chart, and order placement interface.
<img width="1829" height="860" alt="ChatGPT Image Sep 6, 2026, 12_34_47 PM" src="https://github.com/user-attachments/assets/36418a30-15cd-4529-a7ae-cf0d23070a73" />

### Order Book & Recent Trades

The order book displays current bid and ask levels with their available quantities, while the Recent Trades section shows executed market activity.

<img width="1774" height="887" alt="ChatGPT Image Sep 6, 2026, 12_45_11 PM" src="https://github.com/user-attachments/assets/18e6f126-b9a9-4d52-9c9d-9d71eaad8aa9" />

### My Orders

The My Orders section allows users to monitor their submitted orders, including order side, type, price, quantity, filled quantity, status, and cancellation options.

<img width="1840" height="448" alt="Screenshot 2026-09-06 123939" src="https://github.com/user-attachments/assets/324d4e9f-7b43-4bca-ba72-1b3d9de0b9fd" />

### Portfolio & Execution History

The Portfolio section displays account cash, portfolio value, market value, and current positions. Execution History provides a record of completed trades.

<img width="2167" height="702" alt="ChatGPT Image Sep 6, 2026, 12_42_20 PM" src="https://github.com/user-attachments/assets/4f6f62de-47ff-4cea-99b2-7d54d04dd5ab" />

### Grafana Dashboard

Grafana provides monitoring and visualization of exchange performance, order activity, trade execution, and latency metrics.

![Grafana Dashboard](screenshots/grafana-dashboard.png)
