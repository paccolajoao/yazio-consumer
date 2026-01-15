
# 🥑 Yazio Consumer (Clean Architecture)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)

A powerful, privacy-focused desktop application to export your nutritional data from Yazio. Built with **Clean Architecture** principles, it ensures reliability, maintainability, and data accuracy.

Bypasses the limitations of standard exports by communicating directly with the Yazio API to retrieve granular data including **calories, macro-nutrients, and accurate product names**.

---

## ✨ Features

### 🔐 Dual Authentication
*   **Standard Login**: Use your Yazio email and password.
*   **Google Login**: Seamlessly authenticates via Google OAuth (Local Server flow), securing your session without sharing passwords directly.

### ⚡ Smart Data Engine
*   **Parallel Fetching**: Uses multi-threading to download daily logs concurrently, significantly speeding up the process.
*   **Deep Hydration (Two-Pass)**:
    1.  **Scan**: Rapidly scans your meal history to identify consumed items.
    2.  **Hydrate**: Batch-fetches full product details from the API to guarantee 100% accuracy on nutrient values and product names (resolving "Unknown Product" issues).
*   **Resilience**: Automatically handles API timeouts, rate limits, and missing data chunks.

### 📊 Comprehensive Exports
Generates three detailed CSV files in your chosen output folder:
1.  **`nutrition_log.csv`**: Granular log of every single item consumed (Date, Meal Slot, Product, Grams, Calories, Macros).
2.  **`meal_summary.csv`**: Aggregated totals per meal (Breakfast, Lunch, Dinner, Snacks).
3.  **`daily_summary.csv`**: Daily totals for Calories, Protein, Fat, and Carbohydrates.

---

## 🏗️ Architecture

This project is engineered for longevity using **Clean Architecture**.

```mermaid
graph TD
    subgraph "Presentation (UI)"
        UI[Tkinter Window]
    end

    subgraph "Application"
        Login[Login Use Case]
        Export[Export Use Case]
    end

    subgraph "Domain (Core)"
        Models[Entities: DayLog, Product]
        Interfaces[Interfaces: IYazioClient]
    end

    subgraph "Infrastructure"
        API[Yazio Client (API)]
        Auth[Google OAuth Service]
        CSV[CSV Exporter]
    end

    UI --> |Injects| Login
    UI --> |Injects| Export
    Login --> |Uses| Auth
    Export --> |Uses| API
    Export --> |Uses| CSV
    API -- Implements --> Interfaces
```

### directory structure
```text
yazio-consumer/
├── application/         # Pure Business Logic (Use Cases)
├── domain/              # core Entities & Interfaces (No dependencies)
├── infrastructure/      # External adaptations (API, File System, Auth)
├── ui/                  # Presentation Layer (Tkinter)
├── google/              # Credentials storage (Ignored by Git)
├── main.py              # Composition Root (Dependency Injection)
└── requirements.txt     # Dependencies
```

---

## 🚀 Getting Started

### Prerequisites
*   **Python 3.9** or higher.
*   *(Optional)* **Google Credentials** (`credentials.json`) if using Google Login.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/paccolajoao/yazio-consumer.git
    cd yazio-consumer
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the App**:
    ```bash
    python main.py
    ```

---

## 💡 Troubleshooting

### "Unknown Product" or Zero Calories?
This usually happens if the API returns a concise reference instead of the full object.
*   **Fix**: The app now uses a **Two-Pass** strategy. It will automatically detect missing info and fetch the specific product details from the Yazio V9 API. Just run the export again.

### Google Login not working?
*   Ensure you have a valid `google/credentials.json` file from the Google Cloud Console (Desktop App type).
*   If the app opens a browser but doesn't login, check the console logs for URL redirection issues.
*   **Note**: The app no longer auto-opens the browser on startup; you must click "Connect with Google".

---

## 🤝 Contributing

1.  Fork the project.
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the Branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

**Disclaimer**: This is a third-party tool and is not affiliated with Yazio. Use responsibly.
