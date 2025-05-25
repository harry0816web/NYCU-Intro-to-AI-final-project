# Vision-Driven Smart Recipe Recommendation System
**Team:**  Trippa Troppa Tralala Lirilì Rilà Tung Tung Sahur Boneca Tung Tung Tralalelo Trippi Troppa Crocodina

## Introduction
This project develops a smart recipe generation system that starts with an ingredient photo. The system performs ingredient recognition from the image, allows users to input personal preferences and allergen restrictions, and then uses prompt-engineered language models to generate customized and safe recipes based on both the recognized ingredients and user-defined constraints.


## Data
We used the [Kitchen Computer Vision Project](https://universe.roboflow.com/nizarbtk/kitchen-cjfwg) dataset because the ingredients that are more commonly used in our daily life.

## Main Approach
### 1. Ingredient Detection

***Baseline – YOLOv5s Pre-trained Model***

As our starting point, we used the pre-trained YOLOv5s model without any fine-tuning. We tested its performance on 10 real-world photos of ingredients laid out on a table.

***Our Approach – Fine-tuned YOLOv8s Model***

We fine-tuned a YOLOv8s pre-trained model using a custom dataset composed of commonly seen food ingredients. The dataset was collected from Roboflow and labeled using the YOLO format.

To enhance generalization, we applied multiple augmentation techniques such as Mosaic, MixUp, Copy-Paste, rotation, and scaling. 

### 2. Recipe Generation

***Baseline – Gemini API without Prompt Engineering***

We chose **Gemini 2.0 Flash** as our baseline because:

1. **LLMs support creative recipe generation**  
   Gemini, as a large language model, can produce diverse and innovative meal ideas based on user input.

2. **Free, fast, and stable**  
   The Gemini API offers reliable performance without cost, making it accessible and efficient for practical applications.

3. **Easy API integration and user-friendly**  
   The API is straightforward to connect with, and the overall developer experience is smooth and well-documented.

***Our Approach – Gemini with Prompt Engineering + Function Calling***

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
   ![image](https://hackmd.io/_uploads/SkCkSwgfxe.png)
5. If you don't have an account, please **register** and **log in** to the system first.  
After that, you will see the following screen:
![image](https://hackmd.io/_uploads/BJDISwezxl.png)

6. Click on "選擇檔案" to upload your food ingredient photo (.jpg format is recommended for higher accuracy), then click on "Confirm and Recognize Ingredients" to activate the food recognition system.

7. Wait for a moment, and the recognized ingredient list will display the results. If there are any missing ingredients, you can manually add them yourself.
![image](https://hackmd.io/_uploads/ryL6vPxGlg.png)

8. Here are your user preferences. You can customize the recipe based on your dietary preferences and restrictions.
![image](https://hackmd.io/_uploads/Hy4eQclGex.png)

9. Select either "創新料理" or "過往推薦" to decide whether the generated recipe should be based on your previous preferences or created from scratch.  
![image](https://hackmd.io/_uploads/H1DgKqezxe.png)

10. Finally, click on the "生成食譜" button, and you will receive a detailed recipe with step-by-step instructions to guide you through the process.
![image](https://hackmd.io/_uploads/BySBtqxfel.png)

11. At the end of the recipe, you can choose whether you like or dislike the recipe. If you like it, the system will save it and use your feedback to adjust future recipes based on your preferences.
![image](https://hackmd.io/_uploads/S1DwK9eMll.png)

