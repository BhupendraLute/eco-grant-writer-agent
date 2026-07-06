# 💻 Eco Grant Writer Next.js Web App

This is the modern React frontend application for the **Eco Grant Writer** agent, built using **Next.js 16** (App Router), **React 19**, and **Tailwind CSS v4**.

It provides a rich, responsive, and secure user interface that connects directly with the backend FastAPI agent server (`api_server.py`) to coordinate proposal creation.

---

## ✨ Key Features

1. **Intake Chat Interface**: A clean conversational chat area to interact with the agent, complete with custom suggestion chips (such as selecting matched grants or approving/rejecting compliance steps).
2. **Side-by-Side Live Document Preview**: Renders the proposal drafts (individual sections and final compiled markdown) in real-time. Features status indicators showing guideline compliance and security check results.
3. **Persistent State Sidebar**: Displays active metadata parsed from user notes (e.g., location, budget, volunteers, registration ID) and selected grant details so you always know what the agent has extracted.
4. **Interactive Security Approval Modal**: Integrates with the agent's **Human-in-the-Loop (HITL)** security gate. When sensitive data or PII (Aadhaar, PAN, bank accounts, private salaries) is flagged, a modal prompts you to explicitly `Approve` (Bypass) or `Reject` (Abort) the execution.

---

## 🛠️ Tech Stack

* **Framework:** Next.js 16 (App Router)
* **Library:** React 19
* **Styling:** Tailwind CSS v4 & PostCSS
* **Language:** TypeScript

---

## 🚀 Getting Started

### 📋 Prerequisites
Make sure you have Node.js (version 18 or higher) and npm installed. The backend agent server must also be running.

### 1. Install Dependencies
Run the following command inside the `web` directory:
```bash
npm install
```

### 2. Configure Environment (Optional)
By default, the web app connects to the backend at `http://localhost:8000`. You can configure a custom backend URL by creating a `.env.local` file inside the `web` folder:
```env
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

### 3. Run the Development Server
Start the frontend development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the interface.

### 4. Build for Production
To build the application for production deployment:
```bash
npm run build
npm start
```
