# IRWA Final Project 2025 – Part 1  
**Text Processing and Exploratory Data Analysis**

---

## 📁 Repository
GitHub: [https://github.com/laxhoni/IRWA_Final_Project](https://github.com/laxhoni/IRWA_Final_Project)  

---

## 👥 Authors
- **Jhonatan Barcos Gambaro** (u198728)  
- **Daniel Alexander Yearwood Agames** (u214976)

---

## 🧰 How to Run

The project was developed using **Python 3**.

### 1. Clone the Repository & Checkout Tag
First, clone the repository and check out the specific tag for this submission to ensure you are running the exact code that was delivered.

```bash
git clone [https://github.com/laxhoni/IRWA_Final_Project.git](https://github.com/laxhoni/IRWA_Final_Project.git)
cd IRWA_Final_Project
git checkout part-1-submission

Before running the notebook, install the required libraries:
```
### 2. Clone the Repository & Checkout Tag
We strongly recommend using a virtual environment to manage dependencies.

```bash
# Create the environment
python3 -m venv venv

# Activate it (on macOS/Linux)
source venv/bin/activate

# Or activate it (on Windows)
# .\venv\Scripts\activate

```
### 3. Install dependencies
Install the required Python libraries.

```bash
pip install pandas numpy nltk jupyterlab
```

### 4. Download NLTK Resources
Run the following Python command once to download the necessary NLTK packages (punkt for tokenization and stopwords).

```python
import nltk
nltk.download(['punkt', 'stopwords'])
```

### 5. Get Dataset
Download needed dataset **fashion_products_dataset.json** and add it to data folder.

Download link (Aula Global): https://aulaglobal.upf.edu/pluginfile.php/9967944/mod_folder/content/0/fashion_products_dataset.json?forcedownload=1

### 6. Run jupyter notebook
You can now run the notebook to see the full process, from index creation to search results.
```bash
jupyter lab
```
Once Jupyter is open, run all cells in project_part_1.ipynb.



