# 🧠 Overthinker Guide

An AI-powered interactive web application that helps you break down situations you're overthinking into clear, visual outcome scenarios.

## 🎯 What is this?

When you're stuck overthinking a situation, it's hard to see things clearly. This app uses AI to help you:
- Visualize possible outcomes in an interactive tree structure
- Explore **Best Case**, **Expected**, and **Worst Case** scenarios
- Drill down into specific consequences by clicking on nodes
- Gain perspective and clarity on situations causing anxiety

## ✨ Features

- **Interactive Tree Visualization**: Click to expand nodes and explore deeper outcomes
- **AI-Powered Analysis**: Uses Google's Gemini AI to generate realistic scenarios
- **Color-Coded Outcomes**: 
  - 🟢 Green for best case scenarios
  - 🟠 Orange for expected/likely outcomes
  - 🔴 Red for worst case scenarios
- **Perspective Insights**: Get calming, balanced insights about your situation
- **Navigation**: Go back through your exploration history

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- A Google API key (for Gemini AI)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yrstrulyjayanth/overthinker.git
cd overthinker
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or
source .venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API key:
   - Create a `.streamlit` folder if it doesn't exist
   - Create a `secrets.toml` file inside it
   - Add your Google API key:
```toml
GOOGLE_API_KEY = "your-api-key-here"
```

### Running the App

```bash
streamlit run overthinker.py
```

The app will open in your browser at `http://localhost:8501`

## 🎮 How to Use

1. **Describe your situation**: Enter what you're overthinking in the text area
2. **Click "Analyze Outcomes"**: The AI will generate three main outcome branches
3. **Explore branches**: Click any outcome node to see more detailed consequences
4. **Navigate back**: Use the "Go Back" button to return to previous states
5. **Gain perspective**: Read the insight summary at the bottom

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI Model**: Google Gemini (gemini-1.5-flash)
- **Visualization**: streamlit-echarts
- **Language**: Python 3.x

## 📦 Dependencies

- streamlit
- google-generativeai
- streamlit-echarts

## 🔒 Privacy

All your inputs are processed through the Google Gemini API. Please review Google's privacy policy if you have concerns about data handling.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

This project is open source and available for personal and educational use.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- Tree visualization using [ECharts](https://echarts.apache.org/)

---

**Note**: This tool is designed to provide perspective and clarity. For serious mental health concerns, please consult with a qualified mental health professional.
