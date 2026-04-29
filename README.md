# 🚀 AIOps Log Anomaly Detector with AI Explain

An AI-powered DevOps tool that scans logs, detects anomalies, and generates root-cause analysis with suggested fixes using local LLMs (Ollama).

---

## 🔥 Features

* ✅ Detects **CRITICAL / ERROR / WARNING** logs
* 🧠 AI-powered **root cause analysis** (Ollama)
* 📊 Generates structured **incident reports**
* ⚡ Works **offline (local LLM)**
* 📁 Saves report to `docs/report.md`

---

## 🏗️ Architecture

```
Logs → Parser → Anomaly Detection → AI Explain (Ollama) → Report
```

---

## ⚙️ Setup

```bash
git clone https://github.com/imtiaz04/aiops-log-analyzer.git
cd aiops-log-analyzer/demo
python3 -m venv venv
source venv/bin/activate
```

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull gemma:2b
```

---

## ▶️ Usage

### Basic scan

```bash
python3 -m aiops
```

### AI Explain mode

```bash
python3 -m aiops --explain
```

### Save report

```bash
python3 -m aiops --explain --save-report
```

---

## 📄 Sample Output

```
CRITICAL: Out of memory
Fix: Increase memory / optimize process

CRITICAL: Filesystem full
Fix: Cleanup logs / enable log rotation
```

---

## 📂 Project Structure

```
aiops/
├── agent.py
├── cli.py
├── tools.py
├── prompts.py
docs/
├── report.md
logs.txt
```

---

## 🚀 Future Improvements

* 🔔 Slack / Email alerts
* 📊 Grafana integration
* 🐳 Docker log ingestion
* ☁️ AWS CloudWatch support

---

## 👨‍💻 Author

**Imtiaz Shaik**
DevOps Engineer | Cloud | AI

---

