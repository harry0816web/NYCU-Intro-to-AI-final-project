# Vision-Driven Smart Recipe Recommendation System
**Team:**  Trippa Troppa Tralala Lirilì Rilà Tung Tung Sahur Boneca Tung Tung Tralalelo Trippi Troppa Crocodina

## Introduction
This project develops a smart recipe generation system that starts with an ingredient photo. The system performs ingredient recognition from the image, allows users to input personal preferences and allergen restrictions, and then uses prompt-engineered language models to generate customized and safe recipes based on both the recognized ingredients and user-defined constraints.


## Data
We used the [Kitchen Computer Vision Project](https://universe.roboflow.com/nizarbtk/kitchen-cjfwg) dataset because the ingredients that are more commonly used in our daily life.

## Main Approach
### 1. Ingredient Detection

*Baseline – YOLOv5s Pre-trained Model*

As our starting point, we used the pre-trained YOLOv5s model without any fine-tuning. We tested its performance on 10 real-world photos of ingredients laid out on a table.

*Our Approach – Fine-tuned YOLOv8s Model*

We fine-tuned a YOLOv8s pre-trained model using a custom dataset composed of commonly seen food ingredients. The dataset was collected from Roboflow and labeled using the YOLO format.

To enhance generalization, we applied multiple augmentation techniques such as Mosaic, MixUp, Copy-Paste, rotation, and scaling. 

### 2. Recipe Generation

*Baseline – Gemini API without Prompt Engineering*

We initially passed detected ingredients directly into Gemini , resulting in unstructured and generic recipe outputs.

*Our Approach – Gemini with Prompt Engineering + Function Calling*

We applied prompt engineering to guide Gemini in generating structured recipes, and used prompt personalization to tailor responses based on user preferences. Function calling was also integrated to dynamically retrieve user data, making the generation process more consistent, personalized, and extensible.

## Application
In the application directory, you will find our application: a website that can convert ingredient images into detailed step-by-step recipes.
### Usage:
1. Setup Environment
   ```sh
   git clone https://github.com/harry0816web/NYCU-Intro-to-AI-final-project.git
   cd NYCU-Intro-to-AI-final-project
   pip install -r requirements.txt
   ```
2. Insert your Gemini API key in `.env`:
   ```python
   GOOGLE_API_KEY = 'your-api-key-here'
   ```
3. Run `app.py`:
   ```sh
   python app.py
   ```
4. If the application runs successfully, you will see the following screen:
   
