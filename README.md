
# Yazio Exporter (Clean Architecture Edition)

A robust, Clean Architecture-based desktop application for exporting your nutritional data from Yazio to CSV format. This tool supports both standard email/password login and Google Authentication, allowing you to bypass limitations of other exporters and analyze your nutrition data in detail.

## 🌟 Key Features

*   **Clean Architecture**: Built with separation of concerns (Domain, Application, Infrastructure, UI).
*   **Dual Authentication**:
    *   **Password**: Login with your Yazio email and password.
    *   **Google Auth**: Uses local server OAuth flow to obtain tokens securely.
*   **Smart Data Fetching**:
    *   **Parallel Processing**: Fetches days concurrently for speed.
    *   **Two-Pass Logic**: First gathers consumption data, then bulk-fetches full product details to ensure 100% data accuracy (correct names, nutrients).
    *   **Resilient**: Handles missing data, timeouts, and API quirks gracefully.
*   **Comprehensive Exports**:
    *   `nutrition_log.csv`: Detailed log of every item consumed, with precise nutrients.
    *   `meal_summary.csv`: Aggregated calories per meal slot (Breakfast, Lunch, Dinner, Snacks).
    *   `daily_summary.csv`: Daily totals for Calories, Protein, Fat, and Carbs.
*   **Dotenv Support**: easy configuration via `.env` file or UI.

---

## 🏗️ Architecture

This project follows **Clean Architecture** principles to ensure maintainability, testability, and scalability.

```mermaid
graph TD
    subgraph "Presentation Layer"
        UI[Tkinter UI (main_window.py)]
    end

    subgraph "Application Layer"
        Login[LoginUseCase]
        Export[ExportDataUseCase]
    end

    subgraph "Domain Layer"
        Models[Models (DayLog, Product, AuthToken)]
        Interfaces[Interfaces (IYazioClient, IExporter)]
    end

    subgraph "Infrastructure Layer"
        API[YazioClient (API wrapper)]
        Auth[AuthService]
        Google[GoogleOAuthService]
        CSV[CsvExporter]
    end

    %% Dependencies (Arrows point inward/downward)
    UI --> Login
    UI --> Export

    Login --> Auth
    Login --> Google
    Export --> API
    Export --> CSV

    API -- implements --> Interfaces
    CSV -- implements --> Interfaces
    Auth -- uses --> API

    Login -- uses --> Models
    Export -- uses --> Models
    API -- returns --> Models
```

### Layers Description
1.  **Domain (`domain/`)**: The heart of the application. Contains **Entities** (`DayLog`, `Product`) and **Interfaces** (`IYazioClient`, `IExporter`). It has *no external dependencies*.
2.  **Application (`application/`)**: Contains **Use Cases** (`LoginUseCase`, `ExportDataUseCase`). These orchestrate business logic by calling interfaces. They know *what* to do, but not *how* external tools work.
3.  **Infrastructure (`infrastructure/`)**: The implementation details.
    *   `api/yazio_client.py`: Implements `IYazioClient`. Calls Yazio API using `requests`.
    *   `services/google_oauth_service.py`: Handles Google Local OAuth flow.
    *   `exporters/csv_exporter.py`: Implements `IExporter`. Writes CSV files.
4.  **Presentation (`ui/`)**: The user interface. Uses Tkinter to display data and capture user input. It injects dependencies into the Application layer.
5.  **Main (`main.py`)**: The **Composition Root**. It wires everything together.

---

## 🚀 Installation

### Prerequisites
*   Python 3.9+ installed.
*   A Google Cloud Project credentials file (`credentials.json`) if you plan to use Google Login (place it in `google/credentials.json`).

### Steps

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/yazio-exporter.git
    cd yazio-exporter
    ```

2.  **Create a Virtual Environment** (Recommended):
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

4.  **Setup Google Credentials (Optional)**:
    *   Create a project in [Google Cloud Console](https://console.cloud.google.com/).
    *   Enable **Desktop App** OAuth client.
    *   Download `client_secret_....json` and rename it to `credentials.json`.
    *   Place it inside a `google/` folder in the project root.

---

## 🎮 Usage

1.  **Run the Application**:
    ```bash
    python main.py
    ```

2.  **Authentication**:
    *   **Email/Password**: Enter your Yazio credentials securely.
    *   **Google**: Click "Connect with Google". A browser window will open to authorize the app. Once connected, your token is securely exchanged for a Yazio session.

3.  **Export Data**:
    *   Select an **Output Folder**.
    *   Click **Export Data**.
    *   The app will fetch the last 60 days of data and generate CSV files in the selected folder.

---

## 📂 Project Structure

```
yazio-exporter/
├── application/         # Business Logic (Use Cases)
├── dados/               # Default output folder (ignored by git)
├── domain/              # Entities & Interfaces (Pure Python)
├── google/              # Google Credentials (ignored by git)
├── infrastructure/      # API, DB, File implementations
├── legacy/              # Old scripts (reference only)
├── ui/                  # Tkinter User Interface
├── .env                 # Config file (auto-generated)
├── .gitignore           # Git ignore rules
├── main.py              # Entry point
├── README.md            # You are here
└── requirements.txt     # Python dependencies
```

## 🛠️ Development

To modify the project:
1.  Add new business logic in `application/`.
2.  Define new interfaces in `domain/`.
3.  Implement them in `infrastructure/`.
4.  Update `ui/` to expose the new features.

---

**Note**: This tool uses the private API of Yazio and is for personal use only.
