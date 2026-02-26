"""
app.py
======
Entry point for the Skills Gap Analyzer Streamlit app.

Run with:  streamlit run app.py

This launcher delegates to app.streamlit_ui so that the top-level module
name is not "app" (avoiding "No module named 'app.config'; 'app' is not a package").
"""

from app.streamlit_ui import main

if __name__ == "__main__":
    main()
