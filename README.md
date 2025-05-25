# Vision-Driven Smart Recipe Recommendation System
**Team:**  Trippa Troppa Tralala Lirilì Rilà Tung Tung Sahur Boneca Tung Tung Tralalelo Trippi Troppa Crocodina

## Introduction
This project develops a smart recipe generation system that starts with an ingredient photo. The system performs ingredient recognition from the image, allows users to input personal preferences and allergen restrictions, and then uses prompt-engineered language models to generate customized and safe recipes based on both the recognized ingredients and user-defined constraints.


## Data
We used the [Kitchen Computer Vision Project](https://universe.roboflow.com/nizarbtk/kitchen-cjfwg) dataset because the ingredients that are more commonly used in our daily life.

## Main Approach

## Application
In the application directory, you will find our application: a website that can convert ingredient images into detailed step-by-step recipes.
### Usage:
1. Setup Environment
   ```sh
   git clone https://github.com/harry0816web/NYCU-Intro-to-AI-final-project.git
   cd NYCU-Intro-to-AI-final-project
   pip install -r requirements.txt
   ```
2. Insert your Gemini API key in `.env` on line 1:
   ```python
   GOOGLE_API_KEY = 'your-api-key-here'
   ```
3. Run `app.py`:
   ```sh
   python app.py
   ```
4. If the application runs successfully, you will see the following screen:
   
