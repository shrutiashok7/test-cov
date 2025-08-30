# **Test Coverage Analyzer**

**test-cov** is a Streamlit-based tool that helps developers analyze test coverage in Python codebases. It identifies which functions are tested, which are not, and gives clear insights into gaps in testing. Built as part of an internship project to streamline test analysis workflows.

## **Features**

### Code Coverage Analysis
* Upload a zip file of your project or provide a GitHub repo link.
* Parses Python source files to detect all defined functions.
* Identifies which functions are covered by test cases.
* Reports untested functions clearly.

### Tested Functions Report
* Maps test cases to functions.
* Highlights which functions are verified by automated tests.
* Helps ensure critical logic paths are tested.

### GitHub Integration
* Clone repositories directly via URL.
* Supports analyzing Pull Request branches.

### Interactive Web UI
* Built with Streamlit for simplicity and ease of use.
* Clean interface to upload projects, run analysis, and view results instantly.

## **Tech Stack**
* Framework: Streamlit
* Language: Python 3.8+
* Libraries: AST, subprocess, zipfile, shutil, regex
* Version Control: Git (for repo/PR analysis)

## **Project Structure**
test-cov/
│── main.py            # Core Streamlit app for test coverage analysis
│── requirements.txt   # Python dependencies
│── README.md          # Project documentation

## **How It Works**
1. Input – Upload a .zip file of your codebase or provide a GitHub repo link.
2. Extraction/Cloning – The tool extracts files or clones the repo into a temp directory.
3. AST Parsing – Python files are parsed to list all functions.
4. Test Mapping – Functions are checked against test cases.
5. Report – Coverage summary is displayed in the Streamlit UI:
    * ✅ Functions tested
    * ❌ Functions untested

## **Example Workflow**
1. Start the app: streamlit run main.py
2. Upload project.zip or enter https://github.com/username/repo with PR number (optional)
3. View the coverage report showing tested vs. untested functions.
4. Improve your test suite based on the gaps identified! 

