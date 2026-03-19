# 🎓 lecturewithkws — AI-Powered Lecture Assistant

To run the whole app with one click, double-click **`START_APP.bat`** in the root folder.

---

Turn any lecture PDF into a personalised study session. Upload notes → Chat with AI tutor → Practice with quizzes.

---

## 📁 Project Structure

```
lecture-assistant/
├── backend/          # Python FastAPI server
├── frontend/         # React + Vite web app
└── electron-app/     # Desktop wrapper (Electron)
```

---

## 🚀 Quick Start

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

App runs at: **http://localhost:5173**

### 3. Electron Desktop App

```bash
cd electron-app
npm install
npm start
```

> ⚠️ Start the frontend and backend **before** launching Electron.

---

## 🔑 Environment Variables

### `backend/.env`

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Claude API key |
| `PAYSTACK_SECRET_KEY` | Paystack secret key |
| `PAYSTACK_PUBLIC_KEY` | Paystack public key |
| `PAYSTACK_CALLBACK_URL` | URL to redirect after payment |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous key |

### `frontend/.env`

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend URL (default: `http://localhost:8000`) |
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anonymous key |

---

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| **Frontend** | React 19, Vite 7, React Router 7 |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **AI** | Gemini via fals 2.0 |
| **PDF** | pdfplumber |
| **Auth** | Supabase Auth |
| **Payments** | Paystack |
| **Desktop** | Electron |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/upload` | Upload PDF and extract text |
| `POST` | `/chat` | Ask AI a question about notes |
| `POST` | `/quiz` | Generate MCQ quiz from notes |
| `POST` | `/auth/signup` | Register (Supabase) |
| `POST` | `/auth/login` | Login (Supabase) |
| `POST` | `/payments/initialize` | Start Paystack payment |
| `GET` | `/payments/verify/{ref}` | Verify payment |

---

## 💳 Payment Flow

1. User clicks **Upgrade Now** on `/paywall`
2. Frontend calls `POST /payments/initialize` → gets `authorization_url`
3. User is redirected to Paystack checkout
4. On success, Paystack redirects to `PAYSTACK_CALLBACK_URL`
5. Frontend calls `GET /payments/verify/{reference}` to confirm
6. Update user premium status in Supabase

---

## 🔒 Auth Flow

Authentication is handled **client-side** via Supabase JS SDK.
The backend can optionally verify tokens via `SUPABASE_URL` + `SUPABASE_ANON_KEY`.

---

## 📝 License

MIT — built for students, by students.
