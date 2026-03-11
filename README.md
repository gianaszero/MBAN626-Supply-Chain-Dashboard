=============================================================================
MBAN626 DASHBOARD PROJECT: DataCo Global Supply Chain Analytics
=============================================================================

AUTHOR: Gian Carlo Gallon
COURSE: MBAN626 - AI and Data Analytics Strategy
DATE: March 11 2026

1. PROJECT OVERVIEW
-----------------------------------------------------------------------------
This project is an interactive, enterprise-grade business analytics dashboard 
built with Python and Streamlit. It analyzes the "DataCo Global Supply Chain" 
dataset to provide executives with diagnostic insights into logistical efficiency, 
revenue generation, and supply chain risks (such as late deliveries and fraud).

The dashboard features a persistent executive scorecard and dynamic drill-down 
modules (Operational Logistics and Risk & Threat Analysis) driven by an 
Object-Oriented Python architecture.

2. FILES INCLUDED IN THIS SUBMISSION
-----------------------------------------------------------------------------
- app3.py                        : The main Streamlit web application script.
- Dashboard_Notebook.ipynb      : The Jupyter Notebook containing the initial 
                                  data exploration, cleaning steps, and scratchpad.
- DataCoSupplyChainDataset.csv  : The raw dataset (Sourced from Kaggle).
- Final_Report.pdf              : The 1-2 page executive summary and reflection.
- README.txt                    : These instructions.

3. PREREQUISITES AND LIBRARIES
-----------------------------------------------------------------------------
To run this dashboard locally, you must have Python installed along with the 
following libraries:
- streamlit
- pandas
- plotly
- requests

You can install all required libraries at once by opening your terminal or 
command prompt and running:
    pip install streamlit pandas plotly requests

4. HOW TO RUN THE DASHBOARD
-----------------------------------------------------------------------------
Step 1: Extract the submitted ZIP folder to your local machine (e.g., your Desktop).
Step 2: Open your Terminal (Mac/Linux) or Command Prompt / Anaconda Prompt (Windows).
Step 3: Navigate to the extracted folder using the 'cd' command. 
        Example: cd Desktop/MBAN626_Project
Step 4: Execute the following command to launch the app:
        streamlit run app3.py
Step 5: The dashboard will automatically open in your default web browser 
        at http://localhost:8501.

5. EXTERNAL API INTEGRATION
-----------------------------------------------------------------------------
This dashboard integrates the Frankfurter open API (https://api.frankfurter.app) 
to provide live currency conversion for the Executive Scorecard. If the API 
experiences downtime or the user loses internet connection, the application 
features error handling that will gracefully default the dashboard back to USD.
