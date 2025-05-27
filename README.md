# RH-DB

# RecycleHealth Dashboard

**Project Title:** Recycle Health × Duke BIG IDEAs Lab Collaboration
**Timeline:** May 2024 – Sept. 2024
**Team:**

* Sarah Jiang (Pratt ‘25)
* Rachele Manning (Recycle Health)
* Stephanie Sullivan (Duke BIG IDEAs Lab)
* Dr. Jessilyn Dunn (Duke BIG IDEAs Lab)

---

## 🔍 Overview

The RecycleHealth Dashboard is a full-stack web application developed to manage, visualize, and analyze data related to the donation and distribution of wearable health devices. It tracks donors, devices, recipient organizations, and request programs to provide insight into device flow and distribution.

---

## 🚀 Project Goals

* Build a web-based dashboard for storing and querying device donation data
* Enable user-friendly views of donor and organization activity
* Support admins with data upload, editing, and visualization tools

---

## 🛠️ Tech Stack

* **Backend:** Flask (Python)
* **Frontend:** HTML/CSS (Jinja templates)
* **Database (Testing):** SQLite
* **Database (Production):** PostgreSQL
* **Deployment:** [Render](https://render.com)

### 🔗 Source Code

* **Production GitHub repo:** [github.com/sarahhjiang/rh-db](https://github.com/sarahhjiang/rh-db)
* **Testing GitLab repo:** [gitlab.oit.duke.edu/sj344/RH-dashboard](https://gitlab.oit.duke.edu/sj344/RH-dashboard)

---

## 📦 Key Features

* **User Roles:** Public vs Admin, with tailored data views
* **Data Import:** Upload data via Excel (template provided)
* **CRUD Operations:** Add, remove, edit donors, devices, orgs, and requests
* **Search:** Lookup donors, devices, or orgs by name
* **Visualization:** Heatmaps of donor/device locations, request distribution
* **Authentication:** Local user accounts with role-based access
* **Secure (Local Option):** Locally hosted version for sensitive data handling

---

## 🧪 Running the App Locally

### 1. Clone the Repo

```bash
git clone git@github.com:sarahhjiang/rh-db.git
cd rh-db
```

Or download ZIP → open in VSCode → `git pull` for updates.

### 2. Set Up Environment

#### Option 1: Conda with `requirements.txt`

```bash
conda create --name rh-env --file requirements.txt
conda activate rh-env
```

#### Option 2: Manual

```bash
conda create --name rh-env
conda activate rh-env
pip install -r requirements.txt
```

### 3. Run the App

```bash
python3 run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) to view the local app.

To reset the DB:

```bash
python3 reset_db.py
```

---

## ⚠️ Notes

* **Excel Uploads:** Only one sheet per Excel upload. Use provided templates and update one table at a time.
* **Security:** Local deployments do **not** expose data externally. No password complexity required for local-only users.
* **Performance:** Long load times on deployed version — contact Bill for investigation.

---

## 📊 Dashboard Summary Pages

* **Organizations & Requests:** View all orgs, request descriptions, and device fulfillment
* **Donor Overview:** Track all donations and associated devices per donor
* **Plots:**

  * Donors by state
  * Devices by state
  * Request destinations

---